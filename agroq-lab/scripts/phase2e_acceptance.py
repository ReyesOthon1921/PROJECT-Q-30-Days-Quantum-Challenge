"""Generate the AgroQ Phase 2 field-acceptance evidence report.

This command is read-only. It evaluates the local gateway database and runtime
configuration, then writes JSON and Markdown reports for a human release review.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from scripts.phase2e_field_release import (
        load_and_validate as load_field_release,
        validate_field_release,
    )
    from scripts.phase2e_readiness import (
        load_and_validate as load_readiness,
        validate_readiness,
    )
except ModuleNotFoundError:  # Direct execution: python scripts/phase2e_acceptance.py
    from phase2e_field_release import (
        load_and_validate as load_field_release,
        validate_field_release,
    )
    from phase2e_readiness import (
        load_and_validate as load_readiness,
        validate_readiness,
    )


def _count(conn: sqlite3.Connection, sql: str) -> int:
    return int(conn.execute(sql).fetchone()[0])


def _readiness_evidence(summary: dict[str, Any]) -> str:
    readiness = summary["readiness_counts"]
    preflight = summary["preflight_counts"]
    deviations = summary["unresolved_deviations"]
    return (
        f"readiness PASS: {readiness['pass']}/15; "
        f"preflight PASS: {preflight['pass']}/15; "
        f"approvals: {summary['approval_count']}/{summary['required_approval_count']}; "
        f"unresolved deviations: {deviations if deviations is not None else 'invalid'}; "
        f"decision: {summary['decision']}"
    )


def _field_release_evidence(summary: dict[str, Any]) -> str:
    manual = summary["manual_release_counts"]
    deviations = summary["unresolved_deviations"]
    return (
        f"manual release PASS: {manual['pass']}/9; "
        f"approvals: {summary['approval_count']}/{summary['required_approval_count']}; "
        f"unresolved deviations: {deviations if deviations is not None else 'invalid'}; "
        f"decision: {summary['decision']}"
    )


def evaluate(
    db_path: Path,
    deployment_ready: bool,
    readiness_summary: dict[str, Any] | None = None,
    field_release_summary: dict[str, Any] | None = None,
    evidence_mode: str = "unspecified",
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    readiness = readiness_summary or validate_readiness(None)
    field_release = field_release_summary or validate_field_release(None)
    technical_check_ids: set[str] = set()

    def add(
        check_id: str,
        label: str,
        passed: bool,
        evidence: str,
        *,
        technical: bool = False,
    ) -> None:
        checks.append({"id": check_id, "label": label, "passed": passed, "evidence": evidence})
        if technical:
            technical_check_ids.add(check_id)

    field_mode = evidence_mode == "field"
    add(
        "P2E-EVIDENCE-MODE",
        "Verified field evidence mode",
        field_mode,
        f"evidence mode: {evidence_mode}",
        technical=True,
    )
    field_db_name = db_path.name.lower()
    field_db_named_safely = field_mode and not any(
        marker in field_db_name for marker in ("simulation", "rehearsal", "demo")
    )
    add(
        "P2E-FIELD-DB",
        "Dedicated field database naming boundary",
        field_db_named_safely,
        "field database name excludes simulation, rehearsal, and demo markers",
        technical=True,
    )

    if not db_path.exists():
        add("P2E-DB", "Local database is available", False, "Database file is missing", technical=True)
    else:
        try:
            # sqlite3.Connection's context manager commits or rolls back, but it
            # does not close the handle. Use closing so Windows can replace the
            # database immediately after acceptance evaluation.
            with closing(sqlite3.connect(db_path)) as conn:
                outage = _count(conn, "SELECT COUNT(*) FROM outage_tests WHERE status='passed'")
                backups = _count(conn, "SELECT COUNT(*) FROM backup_runs WHERE status='verified'")
                devices = _count(conn, "SELECT COUNT(*) FROM gateway_devices WHERE status!='retired'")
                health = _count(conn, "SELECT COUNT(*) FROM device_health_events")
                observations = _count(conn, "SELECT COUNT(*) FROM observations")
                audit = _count(conn, "SELECT COUNT(*) FROM audit_events")
        except sqlite3.Error:
            add("P2E-DB", "Local database is available", False,
                "Database schema could not be evaluated", technical=True)
        else:
            add("P2E-DB", "Local database is available", True,
                "Database schema evaluated", technical=True)
            add("P2E-OUTAGE", "24-hour outage acceptance", outage > 0,
                f"passed records: {outage}", technical=True)
            add("P2E-BACKUP", "Verified backup recovery", backups > 0,
                f"verified backups: {backups}", technical=True)
            add("P2E-DEVICE", "Device registry and health history", devices > 0 and health > 0,
                f"active devices: {devices}; health events: {health}", technical=True)
            add("P2E-MANUAL", "Manual field workflow evidence", observations > 0,
                f"observations retained: {observations}", technical=True)
            add("P2E-AUDIT", "Audit trail evidence", audit > 0,
                f"audit events: {audit}", technical=True)
    add("P2E-LAN", "Safe LAN deployment configuration", deployment_ready,
        "gateway_configuration().deployment_ready", technical=True)
    add("P2E-MIGRATION", "Database migration decision recorded", True,
        "SQLite retained for Phase 2; PostgreSQL deferred until documented triggers are met",
        technical=True)
    add(
        "P2E-READINESS",
        "Private preflight readiness authorization",
        bool(readiness["record_valid"] and readiness["ready"]),
        _readiness_evidence(readiness),
    )
    add(
        "MANUAL-RELEASE",
        "Post-field manual release authorization",
        bool(field_release["record_valid"] and field_release["accepted"]),
        _field_release_evidence(field_release),
    )
    campaign_matches = bool(
        readiness.get("campaign_ref_sha256")
        and readiness.get("campaign_ref_sha256") == field_release.get("campaign_ref_sha256")
    )
    add(
        "P2E-CAMPAIGN",
        "Preflight and field-release campaign identity match",
        campaign_matches,
        "sanitized campaign references match" if campaign_matches else "campaign references do not match",
    )

    technical_acceptance = all(
        check["passed"] for check in checks if check["id"] in technical_check_ids
    )
    ready = technical_acceptance and all(
        check["passed"]
        for check in checks
        if check["id"] in {"P2E-READINESS", "MANUAL-RELEASE", "P2E-CAMPAIGN"}
    )
    return {
        "phase": "2E",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_mode": evidence_mode,
        "technical_acceptance_passed": technical_acceptance,
        "release_status": "ready_for_phase3" if ready else "blocked",
        "phase3_sensor_integration_allowed": ready,
        "checks": checks,
        "readiness_summary": readiness,
        "field_release_summary": field_release,
    }


def markdown(report: dict[str, Any]) -> str:
    rows = ["# AgroQ Phase 2E Field Acceptance Report", "",
            f"Release status: **{report['release_status']}**", "",
            "| Gate | Acceptance item | Result | Evidence |", "|---|---|---|---|"]
    for check in report["checks"]:
        result = "PASS" if check["passed"] else "BLOCKED"
        evidence = check["evidence"].replace("|", "/")
        rows.append(f"| {check['id']} | {check['label']} | {result} | {evidence} |")
    rows += ["", "Phase 3 physical-sensor integration is permitted only when every gate passes.", ""]
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=os.getenv("AGROQ_DB_PATH", "agroq.db"))
    parser.add_argument("--output", default="results/phase2e")
    parser.add_argument(
        "--readiness",
        default=os.getenv("AGROQ_PHASE2E_READINESS_PATH"),
        help="Path to the private Phase 2E readiness-summary JSON file",
    )
    parser.add_argument(
        "--field-release",
        default=os.getenv("AGROQ_PHASE2E_FIELD_RELEASE_PATH"),
        help="Path to the private post-field release-summary JSON file",
    )
    parser.add_argument(
        "--evidence-mode",
        choices=("field", "simulation", "unspecified"),
        default="unspecified",
    )
    args = parser.parse_args()
    from app import gateway_configuration

    readiness = (
        load_readiness(Path(args.readiness))
        if args.readiness
        else validate_readiness(None)
    )
    field_release = (
        load_field_release(Path(args.field_release))
        if args.field_release
        else validate_field_release(None)
    )
    report = evaluate(
        Path(args.db),
        bool(gateway_configuration()["deployment_ready"]),
        readiness_summary=readiness,
        field_release_summary=field_release,
        evidence_mode=args.evidence_mode,
    )
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase2e_acceptance.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output / "phase2e_acceptance.md").write_text(markdown(report), encoding="utf-8")
    print(f"Phase 2E: {report['release_status']}")
    return 0 if report["phase3_sensor_integration_allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
