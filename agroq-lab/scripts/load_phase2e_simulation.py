"""Load deterministic Phase 2E rehearsal evidence into a simulation database.

This loader is intentionally limited to synthetic evidence. It must never be
used with a production or verified-field database.
"""

from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


SIMULATION_FILENAME_TOKEN = "simulation"


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def require_simulation_database(path: Path) -> None:
    if SIMULATION_FILENAME_TOKEN not in path.name.lower():
        raise SystemExit(
            "Refusing to continue: database filename must contain "
            f"'{SIMULATION_FILENAME_TOKEN}'."
        )
    if not path.is_file():
        raise SystemExit(f"Simulation database not found: {path}")


def required_tables_exist(connection: sqlite3.Connection) -> None:
    required = {
        "users",
        "outage_tests",
        "outage_checkpoints",
        "backup_runs",
        "gateway_devices",
        "device_health_events",
        "audit_events",
    }
    present = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    missing = sorted(required - present)
    if missing:
        raise SystemExit("Missing required tables: " + ", ".join(missing))


def select_rehearsal_user(connection: sqlite3.Connection) -> str:
    row = connection.execute(
        """
        SELECT user_id
        FROM users
        WHERE active = 1
        ORDER BY CASE role WHEN 'administrator' THEN 0 ELSE 1 END, created_at
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        raise SystemExit(
            "No active user exists in the simulation database. "
            "Create the normal simulation user through the application first."
        )
    return str(row[0])


def load_evidence(connection: sqlite3.Connection, user_id: str) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    outage_start = now - timedelta(hours=25)
    checkpoints = (
        ("phase2e-sim-checkpoint-00h", outage_start),
        ("phase2e-sim-checkpoint-08h", outage_start + timedelta(hours=8)),
        ("phase2e-sim-checkpoint-16h", outage_start + timedelta(hours=16)),
        ("phase2e-sim-checkpoint-24h", outage_start + timedelta(hours=24)),
    )

    connection.execute(
        """
        INSERT INTO outage_tests (
            outage_test_id, status, started_at, started_by,
            completed_at, completed_by, notes, result_notes
        ) VALUES (?, 'passed', ?, ?, ?, ?, ?, ?)
        ON CONFLICT(outage_test_id) DO UPDATE SET
            status = excluded.status,
            started_at = excluded.started_at,
            started_by = excluded.started_by,
            completed_at = excluded.completed_at,
            completed_by = excluded.completed_by,
            notes = excluded.notes,
            result_notes = excluded.result_notes
        """,
        (
            "phase2e-sim-outage-24h",
            iso(outage_start),
            user_id,
            iso(now),
            user_id,
            "Synthetic Phase 2E outage rehearsal; not field evidence.",
            "Passed 24-hour simulation with database, manual workflow, and backup checks.",
        ),
    )

    for checkpoint_id, recorded_at in checkpoints:
        connection.execute(
            """
            INSERT INTO outage_checkpoints (
                checkpoint_id, outage_test_id, recorded_at,
                database_ok, manual_workflow_ok, backup_ok, notes, recorded_by
            ) VALUES (?, 'phase2e-sim-outage-24h', ?, 1, 1, 1, ?, ?)
            ON CONFLICT(checkpoint_id) DO UPDATE SET
                outage_test_id = excluded.outage_test_id,
                recorded_at = excluded.recorded_at,
                database_ok = excluded.database_ok,
                manual_workflow_ok = excluded.manual_workflow_ok,
                backup_ok = excluded.backup_ok,
                notes = excluded.notes,
                recorded_by = excluded.recorded_by
            """,
            (
                checkpoint_id,
                iso(recorded_at),
                "Synthetic checkpoint; not field evidence.",
                user_id,
            ),
        )

    connection.execute(
        """
        INSERT INTO backup_runs (
            backup_id, filename, trigger_type, status, size_bytes,
            verification_message, created_by, created_at, verified_at
        ) VALUES (?, ?, 'automatic', 'verified', ?, ?, ?, ?, ?)
        ON CONFLICT(backup_id) DO UPDATE SET
            filename = excluded.filename,
            trigger_type = excluded.trigger_type,
            status = excluded.status,
            size_bytes = excluded.size_bytes,
            verification_message = excluded.verification_message,
            created_by = excluded.created_by,
            created_at = excluded.created_at,
            verified_at = excluded.verified_at
        """,
        (
            "phase2e-sim-backup",
            "phase2e_simulation_verified.sqlite3",
            4096,
            "Synthetic restore verification passed; no physical field evidence.",
            user_id,
            iso(outage_start + timedelta(hours=12)),
            iso(outage_start + timedelta(hours=12, minutes=5)),
        ),
    )

    connection.execute(
        """
        INSERT INTO gateway_devices (
            device_id, name, device_type, network_address, status,
            firmware_version, notes, last_seen_at, registered_by, registered_at
        ) VALUES (?, ?, ?, ?, 'online', ?, ?, ?, ?, ?)
        ON CONFLICT(device_id) DO UPDATE SET
            name = excluded.name,
            device_type = excluded.device_type,
            network_address = excluded.network_address,
            status = excluded.status,
            firmware_version = excluded.firmware_version,
            notes = excluded.notes,
            last_seen_at = excluded.last_seen_at,
            registered_by = excluded.registered_by,
            registered_at = excluded.registered_at
        """,
        (
            "phase2e-sim-device",
            "Phase 2E simulated gateway device",
            "simulated_sensor_node",
            "sim://phase2e/device/1",
            "sim-1.0.0",
            "Synthetic device record; no physical hardware connected.",
            iso(now),
            user_id,
            iso(outage_start),
        ),
    )

    connection.execute(
        """
        INSERT INTO device_health_events (
            health_event_id, device_id, event_type, previous_status,
            reported_status, diagnostic_result, battery_percent,
            signal_quality, firmware_version, notes, recorded_by, recorded_at
        ) VALUES (?, 'phase2e-sim-device', 'inspection', 'registered',
                  'online', 'pass', 100, 100, ?, ?, ?, ?)
        ON CONFLICT(health_event_id) DO UPDATE SET
            device_id = excluded.device_id,
            event_type = excluded.event_type,
            previous_status = excluded.previous_status,
            reported_status = excluded.reported_status,
            diagnostic_result = excluded.diagnostic_result,
            battery_percent = excluded.battery_percent,
            signal_quality = excluded.signal_quality,
            firmware_version = excluded.firmware_version,
            notes = excluded.notes,
            recorded_by = excluded.recorded_by,
            recorded_at = excluded.recorded_at
        """,
        (
            "phase2e-sim-health",
            "sim-1.0.0",
            "Synthetic health inspection; no physical hardware connected.",
            user_id,
            iso(now),
        ),
    )

    connection.execute(
        """
        INSERT INTO audit_events (
            audit_id, user_id, action, entity_type, entity_id, details, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(audit_id) DO UPDATE SET
            user_id = excluded.user_id,
            action = excluded.action,
            entity_type = excluded.entity_type,
            entity_id = excluded.entity_id,
            details = excluded.details,
            created_at = excluded.created_at
        """,
        (
            "phase2e-sim-audit",
            user_id,
            "simulation_rehearsal_loaded",
            "phase2e_acceptance",
            "phase2e-simulation",
            "Synthetic Phase 2E evidence loaded; field authorization remains prohibited.",
            iso(now),
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load protected synthetic evidence for Phase 2E acceptance."
    )
    parser.add_argument(
        "--db",
        default=r"instance\agroq_phase2_simulation.db",
        help="Path to a simulation-only SQLite database.",
    )
    args = parser.parse_args()
    database_path = Path(args.db).expanduser().resolve()
    require_simulation_database(database_path)

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        required_tables_exist(connection)
        user_id = select_rehearsal_user(connection)
        with connection:
            load_evidence(connection, user_id)

    print("Phase 2E synthetic rehearsal evidence loaded.")
    print("Evidence mode remains simulation; physical Phase 3 remains blocked.")


if __name__ == "__main__":
    main()
