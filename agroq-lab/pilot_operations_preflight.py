from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pilot_operations import (
    Q20_Q22_SCHEMA_VERSION,
    REQUIRED_ACKNOWLEDGMENTS,
    REQUIRED_ONBOARDING_CHECKS,
    ensure_pilot_operations_schema,
)

REQUIRED_DOCS = (
    "Q20_CONTROLLED_PILOT_ACTIVATION.md",
    "Q21_FEEDBACK_INCIDENT_AND_SUPPORT_RUNBOOK.md",
    "Q22_PILOT_EVIDENCE_AND_EXIT_DECISION.md",
    "Q20_Q22_ARCHITECTURE_AND_BOUNDARIES.md",
)

EXPECTED_TABLES = {
    "pilot_enrollments",
    "pilot_onboarding_checks",
    "pilot_acknowledgments",
    "pilot_status_events",
    "pilot_feedback",
    "pilot_feedback_reviews",
    "pilot_incidents",
    "pilot_incident_events",
    "pilot_metric_observations",
    "pilot_exit_decisions",
    "pilot_evidence_exports",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def isolated_connection(agroq_root: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE users(
            user_id TEXT PRIMARY KEY,
            username TEXT,
            display_name TEXT,
            password_hash TEXT,
            role TEXT,
            site_id TEXT,
            active INTEGER,
            created_at TEXT
        );
        CREATE TABLE backup_runs(
            backup_id TEXT PRIMARY KEY,
            filename TEXT,
            trigger_type TEXT,
            status TEXT,
            size_bytes INTEGER,
            verification_message TEXT,
            created_by TEXT,
            created_at TEXT,
            verified_at TEXT
        );
        CREATE TABLE quantum_validation_events(
            validation_id TEXT PRIMARY KEY,
            run_id TEXT,
            dataset_id TEXT,
            gate_type TEXT,
            status TEXT,
            message TEXT,
            report_json TEXT,
            evaluated_by TEXT,
            created_at TEXT
        );
        """
    )
    conn.executescript(
        (agroq_root / "access_schema.sql").read_text(encoding="utf-8")
    )
    conn.executescript(
        (agroq_root / "controlled_beta_schema.sql").read_text(encoding="utf-8")
    )
    ensure_pilot_operations_schema(conn)
    ensure_pilot_operations_schema(conn)
    return conn


def run_preflight(repo_root: Path) -> dict[str, Any]:
    agroq_root = repo_root / "agroq-lab"
    docs_root = agroq_root / "docs"
    checks: list[dict[str, Any]] = []

    missing_docs = [
        name for name in REQUIRED_DOCS if not (docs_root / name).is_file()
    ]
    checks.append(
        {
            "code": "Q20_Q22_DOCUMENTS",
            "passed": not missing_docs,
            "details": {"missing": missing_docs},
        }
    )

    required_files = (
        "pilot_operations.py",
        "pilot_operations_schema.sql",
        "pilot_operations_preflight.py",
        "investor-ui/src/components/PilotOperationsWorkspace.jsx",
        "investor-ui/src/pilot_operations.css",
    )
    missing_files = [
        name for name in required_files if not (agroq_root / name).is_file()
    ]
    checks.append(
        {
            "code": "Q20_Q22_FILES",
            "passed": not missing_files,
            "details": {"missing": missing_files},
        }
    )

    app_text = (agroq_root / "app.py").read_text(encoding="utf-8")
    registry_text = (
        agroq_root
        / "investor-ui"
        / "src"
        / "components"
        / "QuantumRegistryWorkspace.jsx"
    ).read_text(encoding="utf-8")
    checks.append(
        {
            "code": "Q20_Q22_REGISTRATION",
            "passed": (
                "AGROQ_Q20_Q22_PILOT_OPERATIONS" in app_text
                and "Q20–Q22 · Pilot Operations" in registry_text
            ),
            "details": {},
        }
    )

    conn = isolated_connection(agroq_root)
    try:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        checks.append(
            {
                "code": "Q20_Q22_SCHEMA",
                "passed": EXPECTED_TABLES <= tables,
                "details": {"missing": sorted(EXPECTED_TABLES - tables)},
            }
        )
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        checks.append(
            {
                "code": "SQLITE_INTEGRITY",
                "passed": integrity == "ok",
                "details": {"integrity": integrity},
            }
        )
    finally:
        conn.close()

    checks.append(
        {
            "code": "Q20_ACTIVATION_GATES",
            "passed": (
                len(REQUIRED_ONBOARDING_CHECKS) == 6
                and set(REQUIRED_ACKNOWLEDGMENTS)
                == {
                    "data_handling",
                    "human_control",
                    "research_limitations",
                }
            ),
            "details": {
                "onboarding_checks": len(REQUIRED_ONBOARDING_CHECKS),
                "acknowledgments": list(REQUIRED_ACKNOWLEDGMENTS),
            },
        }
    )

    module_text = (agroq_root / "pilot_operations.py").read_text(
        encoding="utf-8"
    )
    checks.append(
        {
            "code": "NO_AUTOMATIC_PROMOTION",
            "passed": (
                '"production_promoted": False' in module_text
                and '"production_promoted": True' not in module_text
            ),
            "details": {
                "production_promotion": "manual release review only",
            },
        }
    )

    passed = all(check["passed"] for check in checks)
    return {
        "schema_version": f"{Q20_Q22_SCHEMA_VERSION}-PREFLIGHT",
        "generated_at": utc_now(),
        "passed": passed,
        "checks": checks,
        "boundaries": [
            "This preflight validates code readiness only.",
            "No remote deployment or production promotion was triggered.",
            "Pilot activation and exit remain administrator decisions.",
            "No physical field integration or automatic equipment control is authorized.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the AgroQ Q20-Q22 pilot-operations preflight."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_preflight(args.repo_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Q20-Q22 pilot-operations preflight passed: {report['passed']}")
    print(f"Report: {args.output}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
