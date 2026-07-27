from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_PATHS = ("/healthz", "/app/")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalized_url(base_url: str, path: str) -> str:
    return urllib.parse.urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))


def check_url(
    url: str,
    *,
    timeout: float = 20.0,
    attempts: int = 3,
    opener: Any = urllib.request.urlopen,
) -> dict[str, Any]:
    errors: list[str] = []
    for attempt in range(1, attempts + 1):
        started = time.perf_counter()
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "AgroQ-Q16-Staging-Smoke/1.0"},
            )
            with opener(request, timeout=timeout) as response:
                body = response.read(2048)
                status = int(response.status)
                elapsed = round(time.perf_counter() - started, 4)
                return {
                    "url": url,
                    "passed": 200 <= status < 400,
                    "status": status,
                    "elapsed_seconds": elapsed,
                    "body_preview": body.decode(
                        "utf-8", errors="replace"
                    )[:500],
                    "attempt": attempt,
                    "errors": errors,
                }
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            errors.append(f"attempt {attempt}: {exc}")
            if attempt < attempts:
                time.sleep(min(2.0 * attempt, 5.0))
    return {
        "url": url,
        "passed": False,
        "status": None,
        "elapsed_seconds": None,
        "body_preview": "",
        "attempt": attempts,
        "errors": errors,
    }


def run_smoke(
    base_url: str,
    paths: tuple[str, ...] = DEFAULT_PATHS,
    *,
    opener: Any = urllib.request.urlopen,
) -> dict[str, Any]:
    checks = [
        check_url(normalized_url(base_url, path), opener=opener)
        for path in paths
    ]
    return {
        "schema_version": "AGROQ-Q16-STAGING-SMOKE-1.0",
        "generated_at": utc_now(),
        "base_url": base_url.rstrip("/"),
        "passed": all(item["passed"] for item in checks),
        "checks": checks,
        "limitations": [
            "This smoke test verifies public HTTP reachability only.",
            "Authenticated Q15 release workflows require a manual staging review.",
            "A successful push does not prove a deployment occurred when auto-deploy is disabled.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify an explicitly deployed AgroQ staging service."
    )
    parser.add_argument("--base-url", required=True)
    parser.add_argument(
        "--path",
        action="append",
        dest="paths",
        help="Additional or replacement path. Repeat as needed.",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    paths = tuple(args.paths) if args.paths else DEFAULT_PATHS
    report = run_smoke(args.base_url, paths)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Staging smoke passed: {report['passed']}")
    print(f"Staging smoke report: {args.output}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
