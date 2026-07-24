from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


BASE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BASE_DIR.parent


def check(condition: bool, label: str, details: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    suffix = f" — {details}" if details else ""
    print(f"[{status}] {label}{suffix}")
    return condition


def main() -> int:
    results: list[bool] = []

    results.append(
        check(
            (BASE_DIR / "production_portal.py").is_file(),
            "Production portal module",
        )
    )
    results.append(
        check(
            (BASE_DIR / "wsgi.py").is_file(),
            "WSGI production entry point",
        )
    )
    results.append(
        check(
            (BASE_DIR / "Dockerfile").is_file(),
            "Dockerfile",
        )
    )
    results.append(
        check(
            (REPO_ROOT / "render.yaml").is_file(),
            "Render Blueprint",
        )
    )
    results.append(
        check(
            (BASE_DIR / "investor-ui" / "dist" / "index.html").is_file(),
            "Professional frontend production build",
            "run npm run build -- --base=/app/ if missing",
        )
    )

    with tempfile.TemporaryDirectory(prefix="agroq-release-") as temp_dir:
        os.environ["AGROQ_DB_PATH"] = str(
            Path(temp_dir) / "agroq-preflight.db"
        )
        os.environ.setdefault(
            "AGROQ_SECRET_KEY",
            "preflight-only-secret-not-for-deployment",
        )
        os.environ["AGROQ_DEPLOYMENT_MODE"] = "production"
        sys.path.insert(0, str(BASE_DIR))

        try:
            from wsgi import app
        except Exception as exc:
            results.append(
                check(False, "Import production application", str(exc))
            )
        else:
            results.append(
                check(True, "Import production application")
            )
            client = app.test_client()

            response = client.get("/healthz")
            results.append(
                check(
                    response.status_code == 200,
                    "Health endpoint",
                    f"HTTP {response.status_code}",
                )
            )

            try:
                health = response.get_json() or {}
            except Exception:
                health = {}
            results.append(
                check(
                    health.get("ok") is True,
                    "Health response body",
                    json.dumps(health),
                )
            )

            response = client.get("/login")
            results.append(
                check(
                    response.status_code == 200,
                    "Login page",
                    f"HTTP {response.status_code}",
                )
            )

            response = client.get("/admin/notifications")
            results.append(
                check(
                    response.status_code in {301, 302, 303, 307, 308},
                    "Administrator route requires authentication",
                    f"HTTP {response.status_code}",
                )
            )

            response = client.get("/app/")
            results.append(
                check(
                    response.status_code in {200, 503},
                    "Professional UI route",
                    f"HTTP {response.status_code}",
                )
            )

    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
            ],
            cwd=BASE_DIR,
            check=False,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except Exception as exc:
        results.append(
            check(False, "Full automated test suite", str(exc))
        )
    else:
        summary = (
            completed.stdout.strip().splitlines()[-1]
            if completed.stdout.strip()
            else completed.stderr.strip()
        )
        results.append(
            check(
                completed.returncode == 0,
                "Full automated test suite",
                summary,
            )
        )

    passed = all(results)
    print()
    print(
        "RELEASE PREFLIGHT: PASS"
        if passed
        else "RELEASE PREFLIGHT: FAIL"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
