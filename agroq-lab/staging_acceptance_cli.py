from __future__ import annotations

import argparse
import http.cookiejar
import json
import secrets
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PUBLIC_ROUTES = (
    ("/healthz", "backend_health"),
    ("/app/", "frontend_overview"),
    ("/access", "access_community"),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def url(base_url: str, path: str) -> str:
    return urllib.parse.urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))


class StagingClient:
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(jar)
        )

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        form: dict[str, str] | None = None,
    ) -> tuple[int, bytes, dict[str, str]]:
        body = None
        headers = {"User-Agent": "AgroQ-Q17-Staging-Acceptance/1.0"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif form is not None:
            body = urllib.parse.urlencode(form).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        request = urllib.request.Request(
            url(self.base_url, path),
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                return (
                    int(response.status),
                    response.read(),
                    dict(response.headers.items()),
                )
        except urllib.error.HTTPError as exc:
            return int(exc.code), exc.read(), dict(exc.headers.items())

    def get_json(self, path: str) -> dict[str, Any]:
        status, body, _ = self.request("GET", path)
        if not 200 <= status < 300:
            raise RuntimeError(f"GET {path} failed with HTTP {status}.")
        return json.loads(body.decode("utf-8"))

    def post_json(
        self,
        path: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        status, body, _ = self.request("POST", path, payload=payload)
        decoded = json.loads(body.decode("utf-8") or "{}")
        if not 200 <= status < 300:
            raise RuntimeError(
                decoded.get("error") or f"POST {path} failed with HTTP {status}."
            )
        return decoded

    def login(self, username: str, password: str) -> None:
        status, _, _ = self.request(
            "POST",
            "/login",
            form={"username": username, "password": password},
        )
        if status not in {200, 302, 303}:
            raise RuntimeError(f"Staging login failed with HTTP {status}.")
        session = self.get_json("/api/access/session")
        if not session.get("authenticated"):
            raise RuntimeError("Staging session is not authenticated.")


def public_smoke(client: StagingClient) -> list[dict[str, Any]]:
    checks = []
    for path, code in PUBLIC_ROUTES:
        status, body, _ = client.request("GET", path)
        checks.append(
            {
                "check_code": code,
                "path": path,
                "status": status,
                "passed": 200 <= status < 400,
                "body_sha256": __import__("hashlib").sha256(body).hexdigest(),
            }
        )
    return checks


def prepare(
    client: StagingClient,
    *,
    username: str,
    password: str,
    commit_sha: str,
    release_tag: str,
    service_id: str,
    state_path: Path,
) -> dict[str, Any]:
    smoke = public_smoke(client)
    client.login(username, password)

    created = client.post_json(
        "/api/beta/staging-candidates",
        {
            "commit_sha": commit_sha,
            "release_tag": release_tag,
            "backend_url": client.base_url,
            "frontend_url": url(client.base_url, "/app/"),
            "service_id": service_id,
            "notes": "Prepared by the Q17 staging acceptance CLI.",
        },
    )["candidate"]
    candidate_id = created["candidate_id"]

    client.post_json(
        f"/api/beta/staging-candidates/{candidate_id}/deployment",
        {
            "status": "verifying",
            "backend_url": client.base_url,
            "frontend_url": url(client.base_url, "/app/"),
            "service_id": service_id,
        },
    )

    for item in smoke:
        client.post_json(
            f"/api/beta/staging-candidates/{candidate_id}/checks",
            {
                "check_code": item["check_code"],
                "status": "passed" if item["passed"] else "failed",
                "evidence_reference": item["path"],
                "evidence_sha256": item["body_sha256"],
                "notes": f"HTTP {item['status']} recorded by staging CLI.",
            },
        )

    sentinel_key = f"q17-{secrets.token_hex(8)}"
    sentinel_value = secrets.token_urlsafe(32)
    sentinel = client.post_json(
        f"/api/beta/staging-candidates/{candidate_id}/sentinels",
        {
            "sentinel_key": sentinel_key,
            "sentinel_value": sentinel_value,
        },
    )["sentinel"]
    before = client.post_json(
        (
            f"/api/beta/staging-candidates/{candidate_id}/sentinels/"
            f"{sentinel['sentinel_id']}/observe"
        ),
        {
            "phase": "before_restart",
            "observed_value": sentinel_value,
            "notes": "Initial persistence observation.",
        },
    )["observation"]

    state = {
        "schema_version": "AGROQ-Q17-STAGING-STATE-1.0",
        "generated_at": utc_now(),
        "base_url": client.base_url,
        "candidate_id": candidate_id,
        "sentinel_id": sentinel["sentinel_id"],
        "sentinel_key": sentinel_key,
        "sentinel_value": sentinel_value,
        "commit_sha": commit_sha,
        "release_tag": release_tag,
        "service_id": service_id,
        "public_smoke": smoke,
        "before_restart": before,
        "next_action": (
            "Restart or redeploy staging explicitly, then run verify mode."
        ),
    }
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(state, indent=2) + "\n",
        encoding="utf-8",
    )
    return state


def verify(
    client: StagingClient,
    *,
    username: str,
    password: str,
    state_path: Path,
    phase: str,
    output_path: Path,
) -> dict[str, Any]:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    client.login(username, password)
    smoke = public_smoke(client)

    candidate_id = state["candidate_id"]
    sentinel_id = state["sentinel_id"]
    observation = client.post_json(
        (
            f"/api/beta/staging-candidates/{candidate_id}/sentinels/"
            f"{sentinel_id}/observe"
        ),
        {
            "phase": phase,
            "observed_value": state["sentinel_value"],
            "notes": f"Q17 CLI verification after {phase}.",
        },
    )["observation"]

    detail = client.get_json(
        f"/api/beta/staging-candidates/{candidate_id}"
    )
    report = {
        "schema_version": "AGROQ-Q17-STAGING-VERIFY-1.0",
        "generated_at": utc_now(),
        "phase": phase,
        "base_url": client.base_url,
        "candidate_id": candidate_id,
        "sentinel_observed": bool(observation["observed"]),
        "public_smoke": smoke,
        "candidate": detail["candidate"],
        "acceptance_blockers": detail["acceptance_blockers"],
        "passed": bool(observation["observed"])
        and all(item["passed"] for item in smoke),
        "limitations": [
            "In-app screenshots and manual workflow checks remain human-verified.",
            "This command does not accept or release the staging candidate.",
            "This command does not trigger a deployment.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare or verify an explicitly deployed AgroQ staging service."
    )
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument(
        "--mode",
        choices=("prepare", "verify"),
        required=True,
    )
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--commit-sha")
    parser.add_argument("--release-tag")
    parser.add_argument("--service-id", default="")
    parser.add_argument(
        "--phase",
        choices=("after_restart", "after_redeploy"),
        default="after_restart",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    client = StagingClient(args.base_url)
    if args.mode == "prepare":
        if not args.commit_sha or not args.release_tag:
            parser.error("--commit-sha and --release-tag are required in prepare mode.")
        report = prepare(
            client,
            username=args.username,
            password=args.password,
            commit_sha=args.commit_sha,
            release_tag=args.release_tag,
            service_id=args.service_id,
            state_path=args.state,
        )
        print(f"Prepared candidate: {report['candidate_id']}")
        print(f"State file: {args.state}")
        return 0

    output = args.output or args.state.with_name(
        f"staging_{args.phase}_verification.json"
    )
    report = verify(
        client,
        username=args.username,
        password=args.password,
        state_path=args.state,
        phase=args.phase,
        output_path=output,
    )
    print(f"Staging verification passed: {report['passed']}")
    print(f"Report: {output}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
