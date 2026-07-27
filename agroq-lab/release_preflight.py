from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

REQUIRED_TABLES = frozenset(
    {
        "sites",
        "users",
        "audit_events",
        "backup_runs",
        "quantum_research_sources",
        "quantum_datasets",
        "quantum_dataset_lineage",
        "quantum_experiments",
        "quantum_runs",
        "quantum_solver_results",
        "quantum_artifacts",
        "quantum_reviews",
        "quantum_claim_controls",
        "quantum_validation_events",
        "quantum_replay_checks",
        "quantum_research_operations",
        "quantum_lifecycle_events",
        "quantum_release_checklist_events",
        "quantum_evidence_bundles",
    }
)
DEFAULT_SECRET = "agroq-dev-secret-key-change-before-deployment"
DEFAULT_ADMIN_PASSWORD = "agroq-dev-change-me"


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    details: dict[str, Any]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_command(
    command: list[str],
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
        env=os.environ.copy(),
    )


def git_check(repo_root: Path, allow_dirty: bool) -> CheckResult:
    branch = run_command(["git", "branch", "--show-current"], repo_root)
    head = run_command(["git", "rev-parse", "HEAD"], repo_root)
    status = run_command(["git", "status", "--short"], repo_root)
    passed = (
        branch.returncode == 0
        and head.returncode == 0
        and status.returncode == 0
        and (allow_dirty or not status.stdout.strip())
    )
    return CheckResult(
        "git_repository",
        passed,
        "Git repository and working-tree state validated."
        if passed
        else "Git repository validation failed.",
        {
            "branch": branch.stdout.strip(),
            "head": head.stdout.strip(),
            "dirty": bool(status.stdout.strip()),
            "status": status.stdout.strip(),
            "allow_dirty": allow_dirty,
        },
    )


def dependency_check() -> CheckResult:
    modules = ("flask", "pytest")
    missing = [
        module
        for module in modules
        if importlib.util.find_spec(module) is None
    ]
    return CheckResult(
        "python_dependencies",
        not missing,
        "Required Python dependencies are importable."
        if not missing
        else "Required Python dependencies are missing.",
        {
            "python": sys.version,
            "missing": missing,
        },
    )


def secret_check() -> CheckResult:
    secret = os.environ.get("AGROQ_SECRET_KEY", DEFAULT_SECRET)
    admin_password = os.environ.get(
        "AGROQ_ADMIN_PASSWORD",
        DEFAULT_ADMIN_PASSWORD,
    )
    problems: list[str] = []
    if secret == DEFAULT_SECRET or len(secret) < 20:
        problems.append("AGROQ_SECRET_KEY is default or too short.")
    if (
        admin_password == DEFAULT_ADMIN_PASSWORD
        or admin_password == "admin"
        or len(admin_password) < 12
    ):
        problems.append("AGROQ_ADMIN_PASSWORD is default or too short.")
    debug = os.environ.get("AGROQ_DEBUG", "false").lower()
    if debug in {"1", "true", "yes"}:
        problems.append("AGROQ_DEBUG must be disabled.")
    deployment_mode = os.environ.get(
        "AGROQ_DEPLOYMENT_MODE",
        "development",
    )
    if deployment_mode == "development":
        problems.append("AGROQ_DEPLOYMENT_MODE must not be development.")
    return CheckResult(
        "environment_safety",
        not problems,
        "Deployment environment avoids development defaults."
        if not problems
        else "Unsafe deployment defaults remain.",
        {
            "deployment_mode": deployment_mode,
            "debug": debug,
            "problems": problems,
        },
    )


def parse_render_worker_count(text: str) -> int | None:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "- key: WEB_CONCURRENCY":
            for candidate in lines[index + 1 : index + 5]:
                stripped = candidate.strip()
                if stripped.startswith("value:"):
                    value = stripped.split(":", 1)[1].strip().strip('"')
                    try:
                        return int(value)
                    except ValueError:
                        return None
    return None


def worker_configuration_check(repo_root: Path) -> CheckResult:
    render_path = repo_root / "render.yaml"
    docker_path = repo_root / "agroq-lab" / "Dockerfile"
    problems: list[str] = []
    render_workers = None
    docker_single_worker = False
    if not render_path.is_file():
        problems.append("render.yaml is missing.")
    else:
        render_workers = parse_render_worker_count(
            render_path.read_text(encoding="utf-8")
        )
        if render_workers != 1:
            problems.append("render.yaml must use WEB_CONCURRENCY=1 for SQLite.")
    if not docker_path.is_file():
        problems.append("agroq-lab/Dockerfile is missing.")
    else:
        docker_text = docker_path.read_text(encoding="utf-8")
        docker_single_worker = "${WEB_CONCURRENCY:-1}" in docker_text
        if not docker_single_worker:
            problems.append(
                "Dockerfile must default Gunicorn to one worker for SQLite."
            )
    return CheckResult(
        "sqlite_single_worker",
        not problems,
        "SQLite deployment is constrained to one application worker."
        if not problems
        else "SQLite worker configuration is unsafe.",
        {
            "render_workers": render_workers,
            "docker_single_worker": docker_single_worker,
            "problems": problems,
        },
    )


def storage_check(database_path: Path, backup_path: Path) -> CheckResult:
    problems: list[str] = []
    for path, label in (
        (database_path.parent, "database directory"),
        (backup_path, "backup directory"),
    ):
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / f".q16-write-check-{os.getpid()}"
            probe.write_text("q16", encoding="utf-8")
            probe.unlink()
        except OSError as exc:
            problems.append(f"{label} is not writable: {exc}")
    return CheckResult(
        "storage_writable",
        not problems,
        "Database and backup directories are writable."
        if not problems
        else "Storage validation failed.",
        {
            "database_path": str(database_path),
            "backup_path": str(backup_path),
            "problems": problems,
        },
    )


def schema_check(schema_path: Path, database_path: Path) -> CheckResult:
    problems: list[str] = []
    missing_tables: list[str] = []
    integrity = "not_run"
    try:
        schema = schema_path.read_text(encoding="utf-8")
        database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(database_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.executescript(schema)
            conn.executescript(schema)
            table_rows = conn.execute(
                """SELECT name FROM sqlite_master
                   WHERE type='table'"""
            ).fetchall()
            tables = {row[0] for row in table_rows}
            missing_tables = sorted(REQUIRED_TABLES - tables)
            if missing_tables:
                problems.append("Required database tables are missing.")
            integrity_row = conn.execute("PRAGMA integrity_check").fetchone()
            integrity = integrity_row[0] if integrity_row else "no result"
            if integrity != "ok":
                problems.append("SQLite integrity check did not return ok.")
    except (OSError, sqlite3.Error) as exc:
        problems.append(str(exc))
    return CheckResult(
        "schema_and_database",
        not problems,
        "Schema is idempotent, required tables exist, and SQLite is healthy."
        if not problems
        else "Schema or database validation failed.",
        {
            "schema_path": str(schema_path),
            "database_path": str(database_path),
            "schema_sha256": sha256_file(schema_path)
            if schema_path.is_file()
            else None,
            "missing_tables": missing_tables,
            "integrity": integrity,
            "problems": problems,
        },
    )


def latest_failed_validation_count(conn: sqlite3.Connection) -> int:
    if "quantum_validation_events" not in {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }:
        return 0
    row = conn.execute(
        """WITH ranked AS (
               SELECT run_id, gate_type, status,
                      ROW_NUMBER() OVER (
                          PARTITION BY run_id, gate_type
                          ORDER BY created_at DESC, validation_id DESC
                      ) AS rn
               FROM quantum_validation_events
               WHERE run_id IS NOT NULL
           )
           SELECT COUNT(*) FROM ranked
           WHERE rn=1 AND status='failed'"""
    ).fetchone()
    return int(row[0] if row else 0)


def release_operation_blocker_count(conn: sqlite3.Connection) -> int:
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "quantum_research_operations" not in tables:
        return 0
    row = conn.execute(
        """SELECT COUNT(*) FROM quantum_research_operations
           WHERE lifecycle_state='Approved for research'
             AND released_at IS NULL"""
    ).fetchone()
    return int(row[0] if row else 0)


def application_check(
    agroq_root: Path,
    database_path: Path,
    backup_path: Path,
) -> CheckResult:
    previous_cwd = Path.cwd()
    previous_path = list(sys.path)
    problems: list[str] = []
    details: dict[str, Any] = {}
    try:
        os.environ["AGROQ_DB_PATH"] = str(database_path)
        os.environ["AGROQ_BACKUP_DIR"] = str(backup_path)
        os.environ.setdefault("AGROQ_ADMIN_USERNAME", "q16admin")
        os.environ.setdefault(
            "AGROQ_ADMIN_PASSWORD",
            "q16-local-preflight-password",
        )
        os.chdir(agroq_root)
        sys.path.insert(0, str(agroq_root))

        for name in tuple(sys.modules):
            if name in {"app", "release_readiness"}:
                sys.modules.pop(name, None)

        import app as app_module

        app_module.init_db()
        client = app_module.app.test_client()

        health = client.get("/healthz")
        details["healthz_status"] = health.status_code
        if health.status_code != 200:
            problems.append("/healthz did not return HTTP 200.")

        login = client.post(
            "/login",
            data={
                "username": os.environ["AGROQ_ADMIN_USERNAME"],
                "password": os.environ["AGROQ_ADMIN_PASSWORD"],
            },
            follow_redirects=False,
        )
        details["login_status"] = login.status_code
        if login.status_code not in {302, 303}:
            problems.append("Administrator login failed.")

        quantum_health = client.get("/api/quantum/health")
        details["quantum_health_status"] = quantum_health.status_code
        if quantum_health.status_code != 200:
            problems.append("Quantum backend health check failed.")

        readiness = client.get("/api/release/readiness")
        details["release_readiness_status"] = readiness.status_code
        if readiness.status_code != 200:
            problems.append("Q16 release-readiness endpoint failed.")

        with app_module.get_db() as conn:
            source_count = conn.execute(
                "SELECT COUNT(*) FROM quantum_research_sources"
            ).fetchone()[0]
            details["quantum_source_count"] = source_count
            if source_count < 16:
                problems.append("Quantum research sources were not fully seeded.")
            failed_validations = latest_failed_validation_count(conn)
            details["latest_failed_validations"] = failed_validations
            if failed_validations:
                problems.append(
                    "Latest scientific validation includes failed gates."
                )
            approved_not_released = release_operation_blocker_count(conn)
            details["approved_not_released"] = approved_not_released

        backup = app_module.create_database_backup(
            "manual",
            None,
        )
        details["backup"] = backup
        if backup["status"] != "verified":
            problems.append("Database backup was not verified.")
        else:
            recovered, message = app_module.verify_backup_recovery(
                backup["filename"]
            )
            details["backup_recovery"] = {
                "passed": recovered,
                "message": message,
            }
            if not recovered:
                problems.append("Backup recovery verification failed.")
    except Exception as exc:
        problems.append(f"{type(exc).__name__}: {exc}")
    finally:
        os.chdir(previous_cwd)
        sys.path[:] = previous_path
    return CheckResult(
        "application_runtime",
        not problems,
        "Health, authentication, quantum APIs, source seeding, and backup recovery passed."
        if not problems
        else "Application runtime preflight failed.",
        {**details, "problems": problems},
    )


def optional_command_check(
    name: str,
    command: list[str],
    cwd: Path,
) -> CheckResult:
    completed = run_command(command, cwd)
    passed = completed.returncode == 0
    return CheckResult(
        name,
        passed,
        f"{name} passed." if passed else f"{name} failed.",
        {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout[-12000:],
            "stderr": completed.stderr[-12000:],
        },
    )


def write_report(
    checks: list[CheckResult],
    output_dir: Path,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    passed = all(check.passed for check in checks)
    report = {
        "schema_version": "AGROQ-Q16-PREFLIGHT-1.0",
        "generated_at": utc_now(),
        "passed": passed,
        "checks": [asdict(check) for check in checks],
        "limitations": [
            "Local preflight does not prove a remote deployment completed.",
            "SQLite requires one application worker.",
            "Provider-level persistent storage must be verified before storing real operational records.",
            "Staging smoke verification must run after a deployment is explicitly triggered.",
        ],
    }
    json_path = output_dir / "q16_preflight.json"
    md_path = output_dir / "q16_preflight.md"
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# AgroQ Q16 Release Preflight",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Passed: {'YES' if passed else 'NO'}",
        "",
    ]
    for check in checks:
        lines.extend(
            [
                f"## {check.name}",
                "",
                f"- Result: {'PASS' if check.passed else 'FAIL'}",
                f"- Message: {check.message}",
                "",
                "```json",
                json.dumps(check.details, indent=2, ensure_ascii=False),
                "```",
                "",
            ]
        )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the AgroQ Q16 release preflight."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
    )
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--isolated", action="store_true")
    parser.add_argument("--run-tests", action="store_true")
    parser.add_argument("--run-build", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    agroq_root = repo_root / "agroq-lab"
    schema_path = agroq_root / "schema.sql"

    temp_context: tempfile.TemporaryDirectory[str] | None = None
    if args.isolated:
        temp_context = tempfile.TemporaryDirectory(
            prefix="agroq-q16-preflight-"
        )
        temp_root = Path(temp_context.name)
        database_path = temp_root / "instance" / "agroq.db"
        backup_path = temp_root / "backups"
        output_dir = (
            args.output_dir
            or agroq_root / "results" / "release" / "q16"
        )
    else:
        database_path = Path(
            os.environ.get(
                "AGROQ_DB_PATH",
                agroq_root / "instance" / "agroq.db",
            )
        )
        backup_path = Path(
            os.environ.get(
                "AGROQ_BACKUP_DIR",
                agroq_root / "backups",
            )
        )
        output_dir = (
            args.output_dir
            or agroq_root / "results" / "release" / "q16"
        )

    checks = [
        git_check(repo_root, args.allow_dirty),
        dependency_check(),
        secret_check(),
        worker_configuration_check(repo_root),
        storage_check(database_path, backup_path),
        schema_check(schema_path, database_path),
        application_check(agroq_root, database_path, backup_path),
    ]

    if args.run_tests:
        checks.append(
            optional_command_check(
                "complete_pytest_suite",
                [sys.executable, "-m", "pytest", "-q"],
                agroq_root,
            )
        )
    if args.run_build:
        npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
        if npm:
            checks.append(
                optional_command_check(
                    "vite_production_build",
                    [npm, "run", "build", "--", "--base=/app/"],
                    agroq_root / "investor-ui",
                )
            )
        else:
            checks.append(
                CheckResult(
                    "vite_production_build",
                    False,
                    "npm was not found.",
                    {},
                )
            )

    json_path, md_path = write_report(checks, output_dir)
    passed = all(check.passed for check in checks)
    print(f"Q16 preflight passed: {passed}")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")

    if temp_context is not None:
        temp_context.cleanup()
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
