from __future__ import annotations

import hashlib
import io
import json
import platform
import sqlite3
import sys
import time
import zipfile
from typing import Any, Callable

from quantum_runner import canonical_json, sha256_json
from quantum_validation import (
    evaluate_run_gates,
    record_validation_event,
    replay_run,
)

Q15_SCHEMA_VERSION = "AGROQ-QRESEARCH-OPS-1.0"
Q15_VIEW_ROLES = ("administrator", "researcher", "field_operator", "viewer")
Q15_EDIT_ROLES = ("administrator", "researcher")
Q15_REVIEW_ROLES = ("administrator",)

LIFECYCLE_STATES = (
    "Draft",
    "Registered",
    "Dataset attached",
    "Ready to run",
    "Running",
    "Completed",
    "Failed",
    "Under review",
    "Approved for research",
    "Rejected",
    "Superseded",
    "Released",
)

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "Draft": frozenset({"Registered", "Superseded"}),
    "Registered": frozenset({"Dataset attached", "Superseded"}),
    "Dataset attached": frozenset({"Ready to run", "Superseded"}),
    "Ready to run": frozenset({"Running", "Superseded"}),
    "Running": frozenset({"Completed", "Failed"}),
    "Completed": frozenset({"Under review", "Superseded"}),
    "Failed": frozenset({"Under review", "Superseded"}),
    "Under review": frozenset(
        {"Approved for research", "Rejected", "Completed", "Failed"}
    ),
    "Approved for research": frozenset({"Released", "Superseded"}),
    "Rejected": frozenset({"Superseded"}),
    "Superseded": frozenset(),
    "Released": frozenset({"Superseded"}),
}

DEFAULT_MANUAL_CHECKS = {
    "limitations_disclosed": False,
    "evidence_reviewed": False,
    "rollback_plan_documented": False,
    "release_notes_complete": False,
}


def _json_load(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _new_id(prefix: str) -> str:
    return f"AGQ-{prefix}-{time.time_ns()}"


def _row(conn: sqlite3.Connection, query: str, params: tuple[Any, ...]) -> sqlite3.Row:
    result = conn.execute(query, params).fetchone()
    if result is None:
        raise ValueError("Requested research operation record was not found.")
    return result


def _operation_row(
    conn: sqlite3.Connection,
    operation_id: str,
) -> sqlite3.Row:
    return _row(
        conn,
        "SELECT * FROM quantum_research_operations WHERE operation_id=?",
        (operation_id,),
    )


def _run_row(conn: sqlite3.Connection, run_id: str) -> sqlite3.Row:
    return _row(
        conn,
        "SELECT * FROM quantum_runs WHERE run_id=?",
        (run_id,),
    )


def _experiment_row(
    conn: sqlite3.Connection,
    experiment_id: str,
) -> sqlite3.Row:
    return _row(
        conn,
        "SELECT * FROM quantum_experiments WHERE experiment_id=?",
        (experiment_id,),
    )


def _display_name(conn: sqlite3.Connection, user_id: str | None) -> str | None:
    if not user_id:
        return None
    row = conn.execute(
        "SELECT display_name FROM users WHERE user_id=?",
        (user_id,),
    ).fetchone()
    return row["display_name"] if row else user_id


def _serialize_operation(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    include_history: bool = True,
) -> dict[str, Any]:
    operation = dict(row)
    operation["release_checklist"] = _json_load(
        operation.pop("release_checklist_json", None),
        dict(DEFAULT_MANUAL_CHECKS),
    )
    operation["researcher_name"] = _display_name(
        conn, operation.get("researcher_id")
    )
    operation["reviewer_name"] = _display_name(
        conn, operation.get("reviewer_id")
    )

    if operation.get("run_id"):
        run = conn.execute(
            """SELECT r.*, e.sequence, e.title, e.dataset_id,
                      e.code_commit, e.run_type AS experiment_run_type
               FROM quantum_runs r
               JOIN quantum_experiments e
                 ON e.experiment_id=r.experiment_id
               WHERE r.run_id=?""",
            (operation["run_id"],),
        ).fetchone()
        operation["run"] = dict(run) if run else None
        if operation["run"]:
            operation["run"]["run_budget"] = _json_load(
                operation["run"].pop("run_budget_json", None), {}
            )
            operation["run"]["configuration"] = _json_load(
                operation["run"].pop("configuration_json", None), {}
            )
    else:
        operation["run"] = None

    if include_history:
        history_rows = conn.execute(
            """SELECT h.*, u.display_name AS actor_name
               FROM quantum_lifecycle_events h
               LEFT JOIN users u ON u.user_id=h.actor_id
               WHERE h.operation_id=?
               ORDER BY h.created_at, h.event_id""",
            (operation["operation_id"],),
        ).fetchall()
        history: list[dict[str, Any]] = []
        for item in history_rows:
            event = dict(item)
            event["metadata"] = _json_load(
                event.pop("metadata_json", None), {}
            )
            history.append(event)
        operation["history"] = history

        checklist_rows = conn.execute(
            """SELECT * FROM quantum_release_checklist_events
               WHERE operation_id=?
               ORDER BY created_at DESC""",
            (operation["operation_id"],),
        ).fetchall()
        operation["checklist_history"] = [
            {
                **dict(item),
                "checklist": _json_load(item["checklist_json"], {}),
            }
            for item in checklist_rows
        ]

        bundle_rows = conn.execute(
            """SELECT bundle_id, operation_id, run_id, filename,
                      bundle_sha256, manifest_json, created_by, created_at
               FROM quantum_evidence_bundles
               WHERE operation_id=?
               ORDER BY created_at DESC""",
            (operation["operation_id"],),
        ).fetchall()
        operation["evidence_bundles"] = [
            {
                **dict(item),
                "manifest": _json_load(item["manifest_json"], {}),
            }
            for item in bundle_rows
        ]

    return operation


def _record_lifecycle_event(
    conn: sqlite3.Connection,
    *,
    operation_id: str,
    run_id: str | None,
    from_state: str | None,
    to_state: str,
    reason: str,
    actor_id: str,
    utc_now: Callable[[], str],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event_id = _new_id("QLIFE")
    created_at = utc_now()
    conn.execute(
        """INSERT INTO quantum_lifecycle_events(
            event_id, operation_id, run_id, from_state, to_state,
            reason, actor_id, metadata_json, created_at
        ) VALUES(?,?,?,?,?,?,?,?,?)""",
        (
            event_id,
            operation_id,
            run_id,
            from_state,
            to_state,
            reason,
            actor_id,
            canonical_json(metadata or {}),
            created_at,
        ),
    )
    return {
        "event_id": event_id,
        "operation_id": operation_id,
        "run_id": run_id,
        "from_state": from_state,
        "to_state": to_state,
        "reason": reason,
        "actor_id": actor_id,
        "metadata": metadata or {},
        "created_at": created_at,
    }


def create_research_operation(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    actor_id: str,
    actor_role: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    experiment_id = str(payload.get("experiment_id", "")).strip()
    if not experiment_id:
        raise ValueError("experiment_id is required.")
    _experiment_row(conn, experiment_id)

    researcher_id = str(payload.get("researcher_id") or actor_id).strip()
    if researcher_id != actor_id and actor_role != "administrator":
        raise PermissionError("Only an administrator can assign another researcher.")
    researcher = conn.execute(
        """SELECT 1 FROM users
           WHERE user_id=? AND active=1
             AND role IN ('administrator','researcher')""",
        (researcher_id,),
    ).fetchone()
    if researcher is None:
        raise ValueError("Assigned researcher must be an active researcher or administrator.")

    operation_id = str(
        payload.get("operation_id") or _new_id("QOPS")
    ).strip()
    now = utc_now()
    notes = str(payload.get("research_notes", "")).strip()
    limitations = str(payload.get("limitations", "")).strip()
    conn.execute(
        """INSERT INTO quantum_research_operations(
            operation_id, experiment_id, run_id, lifecycle_state,
            researcher_id, reviewer_id, supersedes_operation_id,
            superseded_by_operation_id, research_notes, limitations,
            release_checklist_json, released_at, created_at, updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            operation_id,
            experiment_id,
            None,
            "Draft",
            researcher_id,
            None,
            None,
            None,
            notes,
            limitations,
            canonical_json(DEFAULT_MANUAL_CHECKS),
            None,
            now,
            now,
        ),
    )
    _record_lifecycle_event(
        conn,
        operation_id=operation_id,
        run_id=None,
        from_state=None,
        to_state="Draft",
        reason="Research operation created.",
        actor_id=actor_id,
        utc_now=utc_now,
        metadata={"experiment_id": experiment_id},
    )
    return _serialize_operation(
        conn, _operation_row(conn, operation_id)
    )


def ensure_run_operation(
    conn: sqlite3.Connection,
    run_id: str,
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    existing = conn.execute(
        "SELECT * FROM quantum_research_operations WHERE run_id=?",
        (run_id,),
    ).fetchone()
    if existing is not None:
        return _serialize_operation(conn, existing)

    run = _run_row(conn, run_id)
    experiment = _experiment_row(conn, run["experiment_id"])
    if run["status"] == "completed":
        state = "Completed"
    elif run["status"] == "failed":
        state = "Failed"
    elif run["status"] == "running":
        state = "Running"
    else:
        state = "Ready to run" if experiment["dataset_id"] else "Registered"

    operation_id = _new_id("QOPS")
    now = utc_now()
    conn.execute(
        """INSERT INTO quantum_research_operations(
            operation_id, experiment_id, run_id, lifecycle_state,
            researcher_id, reviewer_id, supersedes_operation_id,
            superseded_by_operation_id, research_notes, limitations,
            release_checklist_json, released_at, created_at, updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            operation_id,
            run["experiment_id"],
            run_id,
            state,
            run["created_by"],
            None,
            None,
            None,
            "",
            "",
            canonical_json(DEFAULT_MANUAL_CHECKS),
            None,
            now,
            now,
        ),
    )
    _record_lifecycle_event(
        conn,
        operation_id=operation_id,
        run_id=run_id,
        from_state=None,
        to_state=state,
        reason="Research operation initialized from persistent run.",
        actor_id=actor_id,
        utc_now=utc_now,
        metadata={"run_status": run["status"]},
    )
    return _serialize_operation(
        conn, _operation_row(conn, operation_id)
    )


def attach_run_to_operation(
    conn: sqlite3.Connection,
    operation_id: str,
    run_id: str,
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    operation = _operation_row(conn, operation_id)
    if operation["run_id"]:
        raise ValueError("This research operation already has a persistent run.")
    run = _run_row(conn, run_id)
    if run["experiment_id"] != operation["experiment_id"]:
        raise ValueError("Run and research operation must use the same experiment.")

    target_state = {
        "running": "Running",
        "completed": "Completed",
        "failed": "Failed",
    }.get(run["status"], "Ready to run")
    now = utc_now()
    conn.execute(
        """UPDATE quantum_research_operations
           SET run_id=?, lifecycle_state=?, updated_at=?
           WHERE operation_id=?""",
        (run_id, target_state, now, operation_id),
    )
    _record_lifecycle_event(
        conn,
        operation_id=operation_id,
        run_id=run_id,
        from_state=operation["lifecycle_state"],
        to_state=target_state,
        reason="Persistent run attached to research operation.",
        actor_id=actor_id,
        utc_now=utc_now,
        metadata={"run_status": run["status"]},
    )
    return _serialize_operation(
        conn, _operation_row(conn, operation_id)
    )


def update_operation_assignment(
    conn: sqlite3.Connection,
    operation_id: str,
    payload: dict[str, Any],
    *,
    actor_id: str,
    actor_role: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    if actor_role != "administrator":
        raise PermissionError("Only an administrator can change research assignments.")
    operation = _operation_row(conn, operation_id)

    researcher_id = str(
        payload.get("researcher_id") or operation["researcher_id"]
    ).strip()
    reviewer_id = payload.get("reviewer_id")
    reviewer_id = (
        str(reviewer_id).strip()
        if reviewer_id is not None and str(reviewer_id).strip()
        else None
    )
    if reviewer_id and reviewer_id == researcher_id:
        raise ValueError("Researcher and reviewer must be different people.")

    for user_id, roles, label in (
        (researcher_id, ("administrator", "researcher"), "researcher"),
        (reviewer_id, ("administrator",), "reviewer"),
    ):
        if not user_id:
            continue
        placeholders = ",".join("?" for _ in roles)
        exists = conn.execute(
            f"""SELECT 1 FROM users
                WHERE user_id=? AND active=1
                  AND role IN ({placeholders})""",
            (user_id, *roles),
        ).fetchone()
        if exists is None:
            raise ValueError(f"Assigned {label} is not an active authorized user.")

    conn.execute(
        """UPDATE quantum_research_operations
           SET researcher_id=?, reviewer_id=?, updated_at=?
           WHERE operation_id=?""",
        (researcher_id, reviewer_id, utc_now(), operation_id),
    )
    _record_lifecycle_event(
        conn,
        operation_id=operation_id,
        run_id=operation["run_id"],
        from_state=operation["lifecycle_state"],
        to_state=operation["lifecycle_state"],
        reason="Research assignments updated.",
        actor_id=actor_id,
        utc_now=utc_now,
        metadata={
            "researcher_id": researcher_id,
            "reviewer_id": reviewer_id,
        },
    )
    return _serialize_operation(
        conn, _operation_row(conn, operation_id)
    )


def _latest_validation_status(
    conn: sqlite3.Connection,
    run_id: str,
    gate_type: str,
) -> str | None:
    row = conn.execute(
        """SELECT status FROM quantum_validation_events
           WHERE run_id=? AND gate_type=?
           ORDER BY created_at DESC LIMIT 1""",
        (run_id, gate_type),
    ).fetchone()
    return row["status"] if row else None


def _release_checklist(
    conn: sqlite3.Connection,
    operation: sqlite3.Row,
) -> dict[str, Any]:
    manual = {
        **DEFAULT_MANUAL_CHECKS,
        **_json_load(operation["release_checklist_json"], {}),
    }
    run_id = operation["run_id"]
    automatic: dict[str, bool] = {
        "approved_lifecycle": operation["lifecycle_state"]
        in {"Approved for research", "Released"},
        "reviewer_separate": bool(operation["reviewer_id"])
        and operation["reviewer_id"] != operation["researcher_id"],
        "run_completed": False,
        "frozen_dataset_attached": False,
        "scientific_validation_passed": False,
        "deterministic_replay_passed": False,
        "evidence_bundle_generated": False,
        "artifacts_present": False,
        "unsafe_claims_absent": False,
    }

    details: dict[str, Any] = {}
    if run_id:
        run = conn.execute(
            """SELECT r.*, e.dataset_id, e.experiment_id
               FROM quantum_runs r
               JOIN quantum_experiments e
                 ON e.experiment_id=r.experiment_id
               WHERE r.run_id=?""",
            (run_id,),
        ).fetchone()
        if run:
            automatic["run_completed"] = run["status"] == "completed"
            automatic["frozen_dataset_attached"] = bool(run["dataset_id"])
            automatic["scientific_validation_passed"] = (
                _latest_validation_status(
                    conn, run_id, "scientific_release"
                )
                in {"passed", "warning"}
            )
            automatic["deterministic_replay_passed"] = (
                _latest_validation_status(
                    conn, run_id, "deterministic_replay"
                )
                == "passed"
            )
            automatic["evidence_bundle_generated"] = bool(
                conn.execute(
                    """SELECT 1 FROM quantum_evidence_bundles
                       WHERE operation_id=? LIMIT 1""",
                    (operation["operation_id"],),
                ).fetchone()
            )
            automatic["artifacts_present"] = bool(
                conn.execute(
                    """SELECT 1 FROM quantum_artifacts
                       WHERE run_id=? LIMIT 1""",
                    (run_id,),
                ).fetchone()
            )
            controls = conn.execute(
                "SELECT * FROM quantum_claim_controls WHERE run_id=?",
                (run_id,),
            ).fetchone()
            automatic["unsafe_claims_absent"] = bool(
                controls
                and not controls["advantage_claim"]
                and not controls["operational_dependency"]
            )
            details = {
                "run_status": run["status"],
                "dataset_id": run["dataset_id"],
                "scientific_validation_status": _latest_validation_status(
                    conn, run_id, "scientific_release"
                ),
                "replay_status": _latest_validation_status(
                    conn, run_id, "deterministic_replay"
                ),
            }

    complete = all(automatic.values()) and all(manual.values())
    return {
        "operation_id": operation["operation_id"],
        "run_id": run_id,
        "automatic": automatic,
        "manual": manual,
        "complete": complete,
        "details": details,
    }


def record_release_checklist(
    conn: sqlite3.Connection,
    operation_id: str,
    payload: dict[str, Any],
    *,
    actor_id: str,
    actor_role: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    if actor_role != "administrator":
        raise PermissionError("Only an administrator can certify release checks.")
    operation = _operation_row(conn, operation_id)
    manual = {
        **DEFAULT_MANUAL_CHECKS,
        **_json_load(operation["release_checklist_json"], {}),
    }
    submitted = payload.get("manual")
    if not isinstance(submitted, dict):
        raise ValueError("manual checklist values are required.")

    for key in DEFAULT_MANUAL_CHECKS:
        if key in submitted:
            manual[key] = bool(submitted[key])

    conn.execute(
        """UPDATE quantum_research_operations
           SET release_checklist_json=?, updated_at=?
           WHERE operation_id=?""",
        (
            canonical_json(manual),
            utc_now(),
            operation_id,
        ),
    )
    refreshed = _operation_row(conn, operation_id)
    checklist = _release_checklist(conn, refreshed)
    checklist_id = _new_id("QCHECK")
    conn.execute(
        """INSERT INTO quantum_release_checklist_events(
            checklist_id, operation_id, run_id, checklist_json,
            complete, evaluated_by, created_at
        ) VALUES(?,?,?,?,?,?,?)""",
        (
            checklist_id,
            operation_id,
            refreshed["run_id"],
            canonical_json(checklist),
            1 if checklist["complete"] else 0,
            actor_id,
            utc_now(),
        ),
    )
    return {"checklist_id": checklist_id, **checklist}


def _json_file(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            default=str,
        )
        + "\n"
    ).encode("utf-8")


def _deterministic_zip(files: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(
        output,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for filename in sorted(files):
            info = zipfile.ZipInfo(filename)
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, files[filename])
    return output.getvalue()


def build_evidence_bundle(
    conn: sqlite3.Connection,
    operation_id: str,
) -> tuple[bytes, dict[str, Any]]:
    operation_row = _operation_row(conn, operation_id)
    if not operation_row["run_id"]:
        raise ValueError("Attach a persistent run before generating evidence.")
    run_id = operation_row["run_id"]
    run = _run_row(conn, run_id)
    experiment = _experiment_row(conn, run["experiment_id"])

    dataset_manifest: dict[str, Any] | None = None
    lineage: list[dict[str, Any]] = []
    if experiment["dataset_id"]:
        dataset = conn.execute(
            """SELECT dataset_id, name, source_kind, source_tables_json,
                      source_record_ids_json, sha256, record_count,
                      quality_summary_json, permitted_families_json,
                      created_by, created_at, review_status
               FROM quantum_datasets WHERE dataset_id=?""",
            (experiment["dataset_id"],),
        ).fetchone()
        if dataset:
            dataset_manifest = dict(dataset)
            for key in (
                "source_tables_json",
                "source_record_ids_json",
                "quality_summary_json",
                "permitted_families_json",
            ):
                dataset_manifest[key.removesuffix("_json")] = _json_load(
                    dataset_manifest.pop(key), {}
                )
            lineage = [
                dict(item)
                for item in conn.execute(
                    """SELECT source_table, source_record_id, payload_sha256
                       FROM quantum_dataset_lineage
                       WHERE dataset_id=?
                       ORDER BY source_table, source_record_id""",
                    (experiment["dataset_id"],),
                ).fetchall()
            ]

    solver_results: list[dict[str, Any]] = []
    for item in conn.execute(
        """SELECT * FROM quantum_solver_results
           WHERE run_id=? ORDER BY solver_name""",
        (run_id,),
    ).fetchall():
        record = dict(item)
        record["result"] = _json_load(
            record.pop("result_json", None), {}
        )
        solver_results.append(record)

    q14_reviews = [
        dict(item)
        for item in conn.execute(
            """SELECT r.*, u.display_name AS reviewer_name
               FROM quantum_reviews r
               LEFT JOIN users u ON u.user_id=r.reviewer_id
               WHERE r.run_id=? ORDER BY r.reviewed_at""",
            (run_id,),
        ).fetchall()
    ]
    lifecycle = _serialize_operation(
        conn,
        operation_row,
        include_history=True,
    )["history"]
    validations: list[dict[str, Any]] = []
    for item in conn.execute(
        """SELECT * FROM quantum_validation_events
           WHERE run_id=? ORDER BY created_at""",
        (run_id,),
    ).fetchall():
        record = dict(item)
        record["report"] = _json_load(
            record.pop("report_json", None), {}
        )
        validations.append(record)

    controls = conn.execute(
        "SELECT * FROM quantum_claim_controls WHERE run_id=?",
        (run_id,),
    ).fetchone()
    artifacts = conn.execute(
        """SELECT * FROM quantum_artifacts
           WHERE run_id=? ORDER BY filename""",
        (run_id,),
    ).fetchall()

    experiment_payload = dict(experiment)
    for key in (
        "source_ids_json",
        "formulation_json",
        "claim_controls_json",
        "raw_record_json",
    ):
        experiment_payload[key.removesuffix("_json")] = _json_load(
            experiment_payload.pop(key, None), {}
        )

    configuration = {
        "run_id": run_id,
        "experiment_id": run["experiment_id"],
        "algorithm": run["algorithm"],
        "run_type": run["run_type"],
        "seed": run["seed"],
        "run_budget": _json_load(run["run_budget_json"], {}),
        "configuration": _json_load(run["configuration_json"], {}),
        "status": run["status"],
        "result_sha256": run["result_sha256"],
        "runtime_seconds": run["runtime_seconds"],
        "error_message": run["error_message"],
    }
    environment = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "code_commit": experiment["code_commit"],
        "evidence_format": Q15_SCHEMA_VERSION,
    }
    operation = _serialize_operation(
        conn, operation_row, include_history=False
    )

    files: dict[str, bytes] = {
        "README.md": (
            "# AgroQ Quantum Research Evidence Package\n\n"
            f"Operation: {operation_id}\n\n"
            f"Run: {run_id}\n\n"
            "This package preserves frozen data lineage, configuration, "
            "solver outputs, validation history, lifecycle decisions, "
            "claim controls, and immutable evidence artifacts.\n"
        ).encode("utf-8"),
        "experiment.json": _json_file(experiment_payload),
        "dataset_manifest.json": _json_file(dataset_manifest),
        "lineage_records.json": _json_file(lineage),
        "configuration.json": _json_file(configuration),
        "solver_results.json": _json_file(solver_results),
        "review_history.json": _json_file(
            {
                "q14_reviews": q14_reviews,
                "q15_lifecycle": lifecycle,
            }
        ),
        "claim_controls.json": _json_file(
            dict(controls) if controls else None
        ),
        "validation_history.json": _json_file(validations),
        "research_operation.json": _json_file(operation),
        "environment.json": _json_file(environment),
        "failed_run_diagnostics.json": _json_file(
            {
                "run_id": run_id,
                "status": run["status"],
                "error_message": run["error_message"],
                "started_at": run["started_at"],
                "completed_at": run["completed_at"],
            }
        ),
    }
    for artifact in artifacts:
        safe_name = str(artifact["filename"]).replace("\\", "_").replace("/", "_")
        files[f"artifacts/{safe_name}"] = str(
            artifact["content_text"]
        ).encode("utf-8")

    hashes = {
        filename: hashlib.sha256(content).hexdigest()
        for filename, content in sorted(files.items())
    }
    files["SHA256SUMS.txt"] = (
        "".join(
            f"{digest}  {filename}\n"
            for filename, digest in hashes.items()
        )
    ).encode("utf-8")
    bundle_bytes = _deterministic_zip(files)
    manifest = {
        "operation_id": operation_id,
        "run_id": run_id,
        "file_count": len(files),
        "files": {
            filename: hashlib.sha256(content).hexdigest()
            for filename, content in sorted(files.items())
        },
        "bundle_sha256": hashlib.sha256(bundle_bytes).hexdigest(),
    }
    return bundle_bytes, manifest


def store_evidence_bundle(
    conn: sqlite3.Connection,
    operation_id: str,
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> tuple[bytes, dict[str, Any]]:
    bundle_bytes, manifest = build_evidence_bundle(conn, operation_id)
    operation = _operation_row(conn, operation_id)
    bundle_id = _new_id("QBUNDLE")
    filename = f"{operation_id.lower()}-evidence.zip"
    conn.execute(
        """INSERT INTO quantum_evidence_bundles(
            bundle_id, operation_id, run_id, filename,
            bundle_sha256, manifest_json, created_by, created_at
        ) VALUES(?,?,?,?,?,?,?,?)""",
        (
            bundle_id,
            operation_id,
            operation["run_id"],
            filename,
            manifest["bundle_sha256"],
            canonical_json(manifest),
            actor_id,
            utc_now(),
        ),
    )
    return bundle_bytes, {
        "bundle_id": bundle_id,
        "filename": filename,
        **manifest,
    }


def transition_research_operation(
    conn: sqlite3.Connection,
    operation_id: str,
    payload: dict[str, Any],
    *,
    actor_id: str,
    actor_role: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    operation = _operation_row(conn, operation_id)
    current = operation["lifecycle_state"]
    target = str(payload.get("to_state", "")).strip()
    reason = str(payload.get("reason", "")).strip()
    if target not in LIFECYCLE_STATES:
        raise ValueError("A valid Q15 lifecycle state is required.")
    if target not in ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"Transition {current!r} -> {target!r} is not allowed.")
    if not reason:
        raise ValueError("A transition reason is required.")

    run_id = operation["run_id"]
    experiment = _experiment_row(conn, operation["experiment_id"])

    if target == "Dataset attached" and not experiment["dataset_id"]:
        raise ValueError("Attach a frozen dataset before this transition.")
    if target in {"Running", "Completed", "Failed", "Under review",
                  "Approved for research", "Rejected", "Released"} and not run_id:
        raise ValueError("Attach a persistent run before this transition.")

    if target == "Running":
        run = _run_row(conn, run_id)
        if run["status"] not in {"queued", "running"}:
            raise ValueError("The persistent run is not queued or running.")
    if target == "Completed":
        run = _run_row(conn, run_id)
        if run["status"] != "completed":
            raise ValueError("The persistent run has not completed.")
    if target == "Failed":
        run = _run_row(conn, run_id)
        if run["status"] != "failed":
            raise ValueError("The persistent run is not marked failed.")

    reviewer_id = operation["reviewer_id"]
    if target in {"Approved for research", "Rejected", "Released"}:
        if actor_role != "administrator":
            raise PermissionError(
                "Only an administrator can approve, reject, or release research."
            )
        if actor_id == operation["researcher_id"]:
            raise PermissionError(
                "The named researcher cannot approve, reject, or release their own work."
            )
        reviewer_id = actor_id

    if target == "Approved for research":
        replay = replay_run(conn, run_id)
        record_validation_event(
            conn,
            replay,
            user_id=actor_id,
            utc_now=utc_now,
        )
        validation = evaluate_run_gates(
            conn,
            run_id,
            include_replay=False,
        )
        record_validation_event(
            conn,
            validation,
            user_id=actor_id,
            utc_now=utc_now,
        )
        if replay["status"] == "failed" or validation["status"] == "failed":
            raise ValueError(
                "Q14 replay and scientific validation gates must pass before Q15 approval."
            )

    superseded_by_operation_id = operation["superseded_by_operation_id"]
    if target == "Superseded":
        replacement_id = str(
            payload.get("replacement_operation_id", "")
        ).strip()
        if not replacement_id:
            raise ValueError(
                "replacement_operation_id is required when superseding research."
            )
        replacement = _operation_row(conn, replacement_id)
        if replacement["operation_id"] == operation_id:
            raise ValueError("A research operation cannot supersede itself.")
        if replacement["experiment_id"] != operation["experiment_id"]:
            raise ValueError(
                "Superseded and replacement operations must use the same experiment."
            )
        superseded_by_operation_id = replacement_id
        conn.execute(
            """UPDATE quantum_research_operations
               SET supersedes_operation_id=?, updated_at=?
               WHERE operation_id=?""",
            (operation_id, utc_now(), replacement_id),
        )

    if target == "Released":
        checklist = _release_checklist(conn, operation)
        if not checklist["complete"]:
            raise ValueError(
                "The Q15 release checklist must be complete before release."
            )

    notes = str(
        payload.get("research_notes", operation["research_notes"] or "")
    ).strip()
    limitations = str(
        payload.get("limitations", operation["limitations"] or "")
    ).strip()
    if target in {"Under review", "Approved for research", "Released"}:
        if not notes:
            raise ValueError("Research notes are required for review and release.")
        if not limitations:
            raise ValueError("Documented limitations are required for review and release.")

    now = utc_now()
    released_at = now if target == "Released" else operation["released_at"]
    conn.execute(
        """UPDATE quantum_research_operations
           SET lifecycle_state=?, reviewer_id=?,
               superseded_by_operation_id=?, research_notes=?,
               limitations=?, released_at=?, updated_at=?
           WHERE operation_id=?""",
        (
            target,
            reviewer_id,
            superseded_by_operation_id,
            notes,
            limitations,
            released_at,
            now,
            operation_id,
        ),
    )
    _record_lifecycle_event(
        conn,
        operation_id=operation_id,
        run_id=run_id,
        from_state=current,
        to_state=target,
        reason=reason,
        actor_id=actor_id,
        utc_now=utc_now,
        metadata={
            "reviewer_id": reviewer_id,
            "replacement_operation_id": superseded_by_operation_id,
        },
    )
    return _serialize_operation(
        conn, _operation_row(conn, operation_id)
    )


def operation_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute(
        """SELECT * FROM quantum_research_operations
           ORDER BY updated_at DESC"""
    ).fetchall()
    operations = [
        _serialize_operation(conn, row, include_history=False)
        for row in rows
    ]
    counts = {state: 0 for state in LIFECYCLE_STATES}
    for operation in operations:
        counts[operation["lifecycle_state"]] += 1
    experiments = [
        dict(row)
        for row in conn.execute(
            """SELECT experiment_id, sequence, title, status,
                      dataset_id, updated_at
               FROM quantum_experiments
               ORDER BY updated_at DESC LIMIT 100"""
        ).fetchall()
    ]
    runs = [
        dict(row)
        for row in conn.execute(
            """SELECT r.run_id, r.experiment_id, r.status, r.started_at,
                      r.completed_at, r.result_sha256, e.sequence, e.title
               FROM quantum_runs r
               JOIN quantum_experiments e
                 ON e.experiment_id=r.experiment_id
               ORDER BY r.started_at DESC LIMIT 100"""
        ).fetchall()
    ]
    return {
        "schema_version": Q15_SCHEMA_VERSION,
        "states": list(LIFECYCLE_STATES),
        "counts": counts,
        "operations": operations,
        "experiments": experiments,
        "runs": runs,
    }


def register_quantum_research_ops(
    *,
    app: Any,
    get_db: Callable[[], Any],
    utc_now: Callable[[], str],
    record_audit_event: Callable[..., None],
    roles_required: Callable[..., Any],
) -> None:
    from flask import Blueprint, Response, g, jsonify, request

    blueprint = Blueprint("quantum_research_ops", __name__)

    def audit(
        action: str,
        entity_type: str,
        entity_id: str,
        details: dict[str, Any],
    ) -> None:
        record_audit_event(
            g.user["user_id"],
            action,
            entity_type,
            entity_id,
            canonical_json(details),
        )

    @blueprint.get("/api/quantum/operations")
    @roles_required(*Q15_VIEW_ROLES)
    def list_operations() -> Response:
        with get_db() as conn:
            summary = operation_summary(conn)
        return jsonify({"ok": True, **summary})

    @blueprint.post("/api/quantum/operations")
    @roles_required(*Q15_EDIT_ROLES)
    def create_operation() -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        try:
            with get_db() as conn:
                operation = create_research_operation(
                    conn,
                    payload,
                    actor_id=g.user["user_id"],
                    actor_role=g.user["role"],
                    utc_now=utc_now,
                )
        except PermissionError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 403
        except (ValueError, sqlite3.IntegrityError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "quantum_research_operation_created",
            "quantum_research_operation",
            operation["operation_id"],
            {"experiment_id": operation["experiment_id"]},
        )
        return jsonify({"ok": True, "operation": operation}), 201

    @blueprint.post("/api/quantum/runs/<run_id>/operation")
    @roles_required(*Q15_EDIT_ROLES)
    def ensure_operation_for_run(
        run_id: str,
    ) -> tuple[Response, int] | Response:
        try:
            with get_db() as conn:
                operation = ensure_run_operation(
                    conn,
                    run_id,
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 404
        audit(
            "quantum_research_operation_ensured",
            "quantum_run",
            run_id,
            {"operation_id": operation["operation_id"]},
        )
        return jsonify({"ok": True, "operation": operation})

    @blueprint.get("/api/quantum/operations/<operation_id>")
    @roles_required(*Q15_VIEW_ROLES)
    def operation_detail(
        operation_id: str,
    ) -> tuple[Response, int] | Response:
        try:
            with get_db() as conn:
                operation = _serialize_operation(
                    conn, _operation_row(conn, operation_id)
                )
                checklist = _release_checklist(
                    conn, _operation_row(conn, operation_id)
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 404
        return jsonify(
            {
                "ok": True,
                "operation": operation,
                "release_checklist": checklist,
                "allowed_transitions": sorted(
                    ALLOWED_TRANSITIONS[
                        operation["lifecycle_state"]
                    ]
                ),
            }
        )

    @blueprint.post("/api/quantum/operations/<operation_id>/attach-run")
    @roles_required(*Q15_EDIT_ROLES)
    def attach_run(
        operation_id: str,
    ) -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        run_id = str(payload.get("run_id", "")).strip()
        if not run_id:
            return jsonify({"ok": False, "error": "run_id is required."}), 400
        try:
            with get_db() as conn:
                operation = attach_run_to_operation(
                    conn,
                    operation_id,
                    run_id,
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "quantum_research_run_attached",
            "quantum_research_operation",
            operation_id,
            {"run_id": run_id},
        )
        return jsonify({"ok": True, "operation": operation})

    @blueprint.post("/api/quantum/operations/<operation_id>/assign")
    @roles_required(*Q15_REVIEW_ROLES)
    def assign_operation(
        operation_id: str,
    ) -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        try:
            with get_db() as conn:
                operation = update_operation_assignment(
                    conn,
                    operation_id,
                    payload,
                    actor_id=g.user["user_id"],
                    actor_role=g.user["role"],
                    utc_now=utc_now,
                )
        except PermissionError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 403
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "quantum_research_assignments_updated",
            "quantum_research_operation",
            operation_id,
            {
                "researcher_id": operation["researcher_id"],
                "reviewer_id": operation["reviewer_id"],
            },
        )
        return jsonify({"ok": True, "operation": operation})

    @blueprint.post("/api/quantum/operations/<operation_id>/transition")
    @roles_required(*Q15_EDIT_ROLES)
    def transition_operation(
        operation_id: str,
    ) -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        try:
            with get_db() as conn:
                operation = transition_research_operation(
                    conn,
                    operation_id,
                    payload,
                    actor_id=g.user["user_id"],
                    actor_role=g.user["role"],
                    utc_now=utc_now,
                )
        except PermissionError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 403
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 409
        audit(
            "quantum_research_lifecycle_transition",
            "quantum_research_operation",
            operation_id,
            {
                "to_state": operation["lifecycle_state"],
                "run_id": operation["run_id"],
            },
        )
        return jsonify({"ok": True, "operation": operation})

    @blueprint.post("/api/quantum/operations/<operation_id>/checklist")
    @roles_required(*Q15_REVIEW_ROLES)
    def update_checklist(
        operation_id: str,
    ) -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        try:
            with get_db() as conn:
                checklist = record_release_checklist(
                    conn,
                    operation_id,
                    payload,
                    actor_id=g.user["user_id"],
                    actor_role=g.user["role"],
                    utc_now=utc_now,
                )
        except PermissionError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 403
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "quantum_release_checklist_evaluated",
            "quantum_research_operation",
            operation_id,
            {"complete": checklist["complete"]},
        )
        return jsonify({"ok": True, "release_checklist": checklist})

    @blueprint.get("/api/quantum/operations/<operation_id>/evidence.zip")
    @roles_required(*Q15_EDIT_ROLES)
    def download_evidence(
        operation_id: str,
    ) -> tuple[Response, int] | Response:
        try:
            with get_db() as conn:
                bundle_bytes, bundle = store_evidence_bundle(
                    conn,
                    operation_id,
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 409
        audit(
            "quantum_evidence_bundle_generated",
            "quantum_research_operation",
            operation_id,
            {
                "bundle_id": bundle["bundle_id"],
                "bundle_sha256": bundle["bundle_sha256"],
            },
        )
        response = Response(
            bundle_bytes,
            content_type="application/zip",
        )
        response.headers["Content-Disposition"] = (
            f'attachment; filename="{bundle["filename"]}"'
        )
        response.headers["X-AgroQ-SHA256"] = bundle["bundle_sha256"]
        response.headers["X-AgroQ-Bundle-ID"] = bundle["bundle_id"]
        return response

    app.register_blueprint(blueprint)
