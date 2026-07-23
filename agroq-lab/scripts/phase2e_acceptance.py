"""Generate the AgroQ Phase 2 field-acceptance evidence report.

This command is read-only. It evaluates the local gateway database and runtime
configuration, then writes JSON and Markdown reports for human release review.

Evidence modes:
- field: Verified field evidence may authorize Phase 3 sensor integration.
- simulation: Synthetic rehearsal evidence may complete technical checks, but
  it can never authorize physical Phase 3 sensor integration.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EVIDENCE_MODES = ("field", "simulation")


def _count(conn: sqlite3.Connection, sql: str) -> int:
    return int(conn.execute(sql).fetchone()[0])


def evaluate(
    db_path: Path,
    deployment_ready: bool,
    evidence_mode: str = "field",
) -> dict[str, Any]:
    """Evaluate Phase 2E acceptance evidence.

    The default remains ``field`` for compatibility with existing callers and
    tests. Command-line use requires the evidence mode to be stated explicitly.
    """
    if evidence_mode not in EVIDENCE_MODES:
        raise ValueError(
            f"Unsupported evidence mode: {evidence_mode!r}. "
            f"Expected one of: {', '.join(EVIDENCE_MODES)}"
        )

    checks: list[dict[str, Any]] = []

    def add(check_id: str, label: str, passed: bool, evidence: str) -> None:
        checks.append(
            {
                "id": check_id,
                "label": label,
                "passed": passed,
                "evidence": evidence,
            }
        )

    if not db_path.exists():
        add("P2E-DB", "Local database is available", False, f"Missing: {db_path}")
    else:
        # sqlite3.Connection's context manager commits or rolls back, but it
        # does not close the handle. Use closing so Windows can delete or
        # replace the database immediately after acceptance evaluation.
        with closing(sqlite3.connect(db_path)) as conn:
            outage = _count(
                conn,
                "SELECT COUNT(*) FROM outage_tests WHERE status='passed'",
            )
            backups = _count(
                conn,
                "SELECT COUNT(*) FROM backup_runs WHERE status='verified'",
            )
            devices = _count(
                conn,
                "SELECT COUNT(*) FROM gateway_devices WHERE status!='retired'",
            )
            health = _count(conn, "SELECT COUNT(*) FROM device_health_events")
            observations = _count(conn, "SELECT COUNT(*) FROM observations")
            audit = _count(conn, "SELECT COUNT(*) FROM audit_events")

        add(
            "P2E-OUTAGE",
            "24-hour outage acceptance",
            outage > 0,
            f"passed records: {outage}",
        )
        add(
            "P2E-BACKUP",
            "Verified backup recovery",
            backups > 0,
            f"verified backups: {backups}",
        )
        add(
            "P2E-DEVICE",
            "Device registry and health history",
            devices > 0 and health > 0,
            f"active devices: {devices}; health events: {health}",
        )
        add(
            "P2E-MANUAL",
            "Manual field workflow evidence",
            observations > 0,
            f"observations retained: {observations}",
        )
        add(
            "P2E-AUDIT",
            "Audit trail evidence",
            audit > 0,
            f"audit events: {audit}",
        )

    add(
        "P2E-LAN",
        "Safe LAN deployment configuration",
        deployment_ready,
        "gateway_configuration().deployment_ready",
    )
    add(
        "P2E-MIGRATION",
        "Database migration decision recorded",
        True,
        "SQLite retained for Phase 2; PostgreSQL deferred until documented "
        "triggers are met",
    )

    technical_acceptance_passed = all(check["passed"] for check in checks)

    if not technical_acceptance_passed:
        release_status = "blocked"
        phase3_sensor_integration_allowed = False
    elif evidence_mode == "simulation":
        release_status = "simulation_complete_field_validation_required"
        phase3_sensor_integration_allowed = False
    else:
        release_status = "ready_for_phase3"
        phase3_sensor_integration_allowed = True

    return {
        "phase": "2E",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_mode": evidence_mode,
        "technical_acceptance_passed": technical_acceptance_passed,
        "release_status": release_status,
        "phase3_sensor_integration_allowed": phase3_sensor_integration_allowed,
        "checks": checks,
    }


def markdown(report: dict[str, Any]) -> str:
    evidence_mode = report["evidence_mode"]
    technical_result = (
        "PASS" if report["technical_acceptance_passed"] else "BLOCKED"
    )

    rows = [
        "# AgroQ Phase 2E Field Acceptance Report",
        "",
        f"Evidence classification: **{evidence_mode.upper()}**",
        f"Technical acceptance: **{technical_result}**",
        f"Release status: **{report['release_status']}**",
        "",
        "| Gate | Acceptance item | Result | Evidence |",
        "|---|---|---|---|",
    ]

    for check in report["checks"]:
        result = "PASS" if check["passed"] else "BLOCKED"
        evidence = check["evidence"].replace("|", "/")
        rows.append(
            f"| {check['id']} | {check['label']} | {result} | {evidence} |"
        )

    rows.append("")

    if evidence_mode == "simulation":
        rows.extend(
            [
                "> SIMULATION EVIDENCE ONLY: This report records a synthetic "
                "technical rehearsal. It does not constitute verified field "
                "acceptance and cannot authorize physical-sensor integration.",
                "",
            ]
        )

    rows.extend(
        [
            "Phase 3 physical-sensor integration is permitted only when every "
            "gate passes using verified field evidence.",
            "",
        ]
    )
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db",
        default=os.getenv("AGROQ_DB_PATH", "agroq.db"),
    )
    parser.add_argument(
        "--output",
        default="results/phase2e",
        help="Output directory for the JSON and Markdown reports.",
    )
    parser.add_argument(
        "--evidence-mode",
        choices=EVIDENCE_MODES,
        required=True,
        help="Use 'field' for verified field evidence or 'simulation' for a "
        "synthetic rehearsal.",
    )
    args = parser.parse_args()

    from app import gateway_configuration

    report = evaluate(
        Path(args.db),
        bool(gateway_configuration()["deployment_ready"]),
        evidence_mode=args.evidence_mode,
    )

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "phase2e_acceptance.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )
    (output / "phase2e_acceptance.md").write_text(
        markdown(report),
        encoding="utf-8",
    )

    print(f"Phase 2E: {report['release_status']}")
    return 0 if report["phase3_sensor_integration_allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())