from __future__ import annotations

import json
import os
import sqlite3
from typing import Any, Callable


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

Q16_VIEW_ROLES = ("administrator", "researcher", "field_operator", "viewer")
Q16_ADMIN_ROLES = ("administrator",)
Q16_REQUIRED_TABLES = frozenset(
    {
        "backup_runs",
        "quantum_validation_events",
        "quantum_research_operations",
        "quantum_evidence_bundles",
    }
)


def _table_names(conn: sqlite3.Connection) -> set[str]:
    return {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }


def _latest_failed_validations(
    conn: sqlite3.Connection,
) -> list[dict[str, Any]]:
    if "quantum_validation_events" not in _table_names(conn):
        return []
    rows = conn.execute(
        """WITH ranked AS (
               SELECT validation_id, run_id, gate_type, status,
                      message, created_at,
                      ROW_NUMBER() OVER (
                          PARTITION BY run_id, gate_type
                          ORDER BY created_at DESC, validation_id DESC
                      ) AS rn
               FROM quantum_validation_events
               WHERE run_id IS NOT NULL
           )
           SELECT validation_id, run_id, gate_type, status,
                  message, created_at
           FROM ranked
           WHERE rn=1 AND status='failed'
           ORDER BY created_at DESC"""
    ).fetchall()
    return [dict(row) for row in rows]


def collect_release_readiness(
    conn: sqlite3.Connection,
    *,
    gateway: dict[str, Any],
) -> dict[str, Any]:
    tables = _table_names(conn)
    missing_tables = sorted(Q16_REQUIRED_TABLES - tables)

    integrity_row = conn.execute("PRAGMA integrity_check").fetchone()
    integrity = integrity_row[0] if integrity_row else "no result"

    latest_backup = None
    if "backup_runs" in tables:
        row = conn.execute(
            """SELECT backup_id, filename, status, size_bytes,
                      verification_message, created_at, verified_at
               FROM backup_runs
               ORDER BY created_at DESC LIMIT 1"""
        ).fetchone()
        latest_backup = dict(row) if row else None

    failed_validations = _latest_failed_validations(conn)

    operation_counts: dict[str, int] = {}
    if "quantum_research_operations" in tables:
        operation_counts = {
            row["lifecycle_state"]: row["n"]
            for row in conn.execute(
                """SELECT lifecycle_state, COUNT(*) AS n
                   FROM quantum_research_operations
                   GROUP BY lifecycle_state"""
            ).fetchall()
        }

    worker_text = os.environ.get("WEB_CONCURRENCY", "1")
    try:
        workers = int(worker_text)
    except ValueError:
        workers = 0

    checks = [
        {
            "code": "SQLITE_INTEGRITY",
            "passed": integrity == "ok",
            "message": f"SQLite integrity: {integrity}",
        },
        {
            "code": "REQUIRED_TABLES",
            "passed": not missing_tables,
            "message": (
                "Required Q16 tables are present."
                if not missing_tables
                else f"Missing tables: {', '.join(missing_tables)}"
            ),
        },
        {
            "code": "SINGLE_WORKER",
            "passed": workers == 1,
            "message": f"WEB_CONCURRENCY={workers}",
        },
        {
            "code": "DEPLOYMENT_CONFIGURATION",
            "passed": bool(gateway.get("deployment_ready")),
            "message": (
                "Gateway configuration is deployment-ready."
                if gateway.get("deployment_ready")
                else "; ".join(gateway.get("safety_issues", []))
            ),
        },
        {
            "code": "SECRET_CONFIGURED",
            "passed": bool(gateway.get("secret_configured")),
            "message": (
                "Deployment secret is configured."
                if gateway.get("secret_configured")
                else "Deployment secret still uses the development fallback."
            ),
        },
        {
            "code": "VERIFIED_BACKUP",
            "passed": bool(
                latest_backup and latest_backup["status"] == "verified"
            ),
            "message": (
                f"Latest backup {latest_backup['filename']} is verified."
                if latest_backup and latest_backup["status"] == "verified"
                else "No verified backup is currently recorded."
            ),
        },
        {
            "code": "SCIENTIFIC_GATES",
            "passed": not failed_validations,
            "message": (
                "No latest scientific validation is failed."
                if not failed_validations
                else f"{len(failed_validations)} latest validation gate(s) failed."
            ),
        },
    ]
    ready = all(check["passed"] for check in checks)
    return {
        "schema_version": "AGROQ-Q16-READINESS-1.0",
        "ready": ready,
        "checks": checks,
        "database": {
            "engine": gateway.get("database_engine"),
            "path": gateway.get("database_path"),
            "integrity": integrity,
            "missing_tables": missing_tables,
        },
        "runtime": {
            "deployment_mode": gateway.get("deployment_mode"),
            "bind_host": gateway.get("bind_host"),
            "workers": workers,
            "debug_enabled": gateway.get("debug_enabled"),
        },
        "latest_backup": latest_backup,
        "failed_validations": failed_validations,
        "operation_counts": operation_counts,
        "boundaries": [
            "Readiness does not trigger a deployment.",
            "Remote staging verification is recorded separately.",
            "SQLite remains limited to one application worker.",
        ],
    }


def register_release_readiness(
    *,
    app: Any,
    get_db: Callable[[], Any],
    gateway_configuration: Callable[[], dict[str, Any]],
    create_database_backup: Callable[[str, str | None], dict[str, Any]],
    verify_backup_recovery: Callable[[str], tuple[bool, str]],
    record_audit_event: Callable[..., None],
    roles_required: Callable[..., Any],
) -> None:
    from flask import Blueprint, Response, g, jsonify

    blueprint = Blueprint("release_readiness", __name__)

    @blueprint.get("/api/release/readiness")
    @roles_required(*Q16_VIEW_ROLES)
    def release_readiness() -> Response:
        with get_db() as conn:
            payload = collect_release_readiness(
                conn,
                gateway=gateway_configuration(),
            )
        return jsonify({"ok": True, **payload})

    @blueprint.post("/api/release/readiness/backup")
    @roles_required(*Q16_ADMIN_ROLES)
    def release_backup() -> tuple[Response, int] | Response:
        backup = create_database_backup(
            "manual",
            g.user["user_id"],
        )
        recovery_passed = False
        recovery_message = backup["message"]
        if backup["status"] == "verified":
            recovery_passed, recovery_message = verify_backup_recovery(
                backup["filename"]
            )
        record_audit_event(
            g.user["user_id"],
            "q16_release_backup_verified",
            "backup",
            backup["backup_id"],
            canonical_json(
                {
                    "backup": backup,
                    "recovery_passed": recovery_passed,
                    "recovery_message": recovery_message,
                }
            ),
        )
        with get_db() as conn:
            readiness = collect_release_readiness(
                conn,
                gateway=gateway_configuration(),
            )
        status = 200 if backup["status"] == "verified" and recovery_passed else 409
        return (
            jsonify(
                {
                    "ok": status == 200,
                    "backup": backup,
                    "recovery": {
                        "passed": recovery_passed,
                        "message": recovery_message,
                    },
                    "readiness": readiness,
                }
            ),
            status,
        )

    app.register_blueprint(blueprint)
