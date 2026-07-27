from __future__ import annotations

import argparse
import json
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from controlled_beta import (
    DEFAULT_INVITATION_POLICY,
    REQUIRED_DEMO_EVIDENCE,
    REQUIRED_STAGING_CHECKS,
    create_staging_candidate,
)

REQUIRED_DOCS = (
    "Q17_STAGING_ACCEPTANCE_RUNBOOK.md",
    "Q17_RENDER_STAGING_BLUEPRINT.md",
    "Q18_USER_INTERVIEW_SCRIPT.md",
    "Q18_PILOT_DISCOVERY_WORKSHEET.md",
    "Q18_INVITATION_AND_ACCESS_POLICY.md",
    "Q19_CLAIMS_REGISTER_POLICY.md",
    "Q19_DEMO_AND_YC_EVIDENCE.md",
    "CONTROLLED_BETA_ARCHITECTURE_AND_LIMITATIONS.md",
    "CONTROLLED_BETA_PULL_REQUEST.md",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_isolated_connection(agroq_root: Path) -> sqlite3.Connection:
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
    schema = (agroq_root / "controlled_beta_schema.sql").read_text(
        encoding="utf-8"
    )
    conn.executescript(schema)
    conn.executescript(schema)
    conn.execute(
        """INSERT INTO users VALUES(
            'Q17-PREFLIGHT-ADMIN','q17preflight','Q17 Preflight',
            'not-a-login','administrator','AGQ-SITE-001',1,?
        )""",
        (utc_now(),),
    )
    return conn


def run_preflight(repo_root: Path) -> dict[str, Any]:
    agroq_root = repo_root / "agroq-lab"
    docs_root = agroq_root / "docs"
    checks: list[dict[str, Any]] = []

    missing_docs = [
        name for name in REQUIRED_DOCS
        if not (docs_root / name).is_file()
    ]
    checks.append(
        {
            "code": "CONTROLLED_BETA_DOCUMENTS",
            "passed": not missing_docs,
            "details": {"missing": missing_docs},
        }
    )

    required_files = (
        "controlled_beta.py",
        "controlled_beta_schema.sql",
        "controlled_beta_preflight.py",
        "staging_acceptance_cli.py",
        "deployment/staging/frontend.Dockerfile",
        "deployment/staging/nginx.conf.template",
        "investor-ui/src/components/ControlledBetaWorkspace.jsx",
        "investor-ui/src/controlled_beta.css",
    )
    missing_files = [
        name for name in required_files
        if not (agroq_root / name).is_file()
    ]
    checks.append(
        {
            "code": "CONTROLLED_BETA_FILES",
            "passed": not missing_files,
            "details": {"missing": missing_files},
        }
    )

    root_files = ("render.staging.yaml",)
    missing_root_files = [
        name for name in root_files
        if not (repo_root / name).is_file()
    ]
    checks.append(
        {
            "code": "STAGING_BLUEPRINT",
            "passed": not missing_root_files,
            "details": {"missing": missing_root_files},
        }
    )

    conn = make_isolated_connection(agroq_root)
    try:
        candidate = create_staging_candidate(
            conn,
            {
                "commit_sha": "preflight-commit",
                "release_tag": "preflight-tag",
            },
            actor_id="Q17-PREFLIGHT-ADMIN",
            utc_now=utc_now,
        )
        checks.append(
            {
                "code": "STAGING_CHECK_SEED",
                "passed": len(candidate["checks"]) == len(REQUIRED_STAGING_CHECKS),
                "details": {
                    "expected": len(REQUIRED_STAGING_CHECKS),
                    "actual": len(candidate["checks"]),
                },
            }
        )
        checks.append(
            {
                "code": "DEMO_EVIDENCE_SEED",
                "passed": (
                    len(candidate["demo_evidence"])
                    == len(REQUIRED_DEMO_EVIDENCE)
                ),
                "details": {
                    "expected": len(REQUIRED_DEMO_EVIDENCE),
                    "actual": len(candidate["demo_evidence"]),
                },
            }
        )
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        expected_tables = {
            "staging_candidates",
            "staging_acceptance_checks",
            "staging_persistence_sentinels",
            "staging_persistence_observations",
            "staging_acceptance_decisions",
            "beta_contacts",
            "beta_interviews",
            "pilot_discovery_records",
            "claims_register",
            "invitation_policies",
            "demo_evidence_items",
            "yc_update_snapshots",
            "controlled_beta_exports",
        }
        checks.append(
            {
                "code": "CONTROLLED_BETA_SCHEMA",
                "passed": expected_tables <= tables,
                "details": {
                    "missing": sorted(expected_tables - tables),
                },
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

    policy_ok = (
        DEFAULT_INVITATION_POLICY["max_expiry_days"] == 14
        and DEFAULT_INVITATION_POLICY["default_max_uses"] == 1
        and DEFAULT_INVITATION_POLICY["public_administrator_invites"] is False
    )
    checks.append(
        {
            "code": "INVITATION_POLICY_DEFAULTS",
            "passed": policy_ok,
            "details": DEFAULT_INVITATION_POLICY,
        }
    )

    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": "AGROQ-Q17-Q19-PREFLIGHT-1.0",
        "generated_at": utc_now(),
        "passed": passed,
        "checks": checks,
        "boundaries": [
            "This preflight validates code readiness only.",
            "No remote deployment was triggered.",
            "Staging acceptance still requires real remote evidence.",
            "Production and physical field integration remain blocked.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the AgroQ Q17-Q19 controlled-beta preflight."
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
    print(f"Controlled-beta preflight passed: {report['passed']}")
    print(f"Report: {args.output}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
