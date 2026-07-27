from __future__ import annotations

import json
import sqlite3
import time
from typing import Any, Callable

from quantum_runner import canonical_json, run_registered_experiment, sha256_json

Q14_SCHEMA_VERSION = "AGROQ-QVALIDATION-1.0"
Q14_VIEW_ROLES = ("administrator", "researcher", "field_operator", "viewer")
Q14_EXECUTE_ROLES = ("administrator", "researcher")

DATASET_TABLES: dict[str, str] = {
    "plots": "plot_id",
    "observations": "observation_id",
    "samples": "sample_id",
    "treatments": "treatment_id",
    "treatment_assignments": "assignment_id",
    "manual_tasks": "task_id",
    "gateway_devices": "device_id",
    "device_health_events": "health_event_id",
    "experiments": "experiment_id",
    "evidence_attachments": "attachment_id",
}

BASELINE_TOKENS: dict[str, tuple[str, ...]] = {
    "Q2": ("exact", "greedy", "classical"),
    "Q3": ("exact", "greedy", "classical"),
    "Q4": ("exact", "greedy", "classical"),
    "Q5": ("classical", "rbf", "logistic"),
    "Q6": ("persistence", "linear", "classical"),
    "Q7": ("monte_carlo", "monte carlo", "classical"),
    "Q8": ("plant_biomagnetic", "signal_simulator", "classical"),
    "Q9": ("exact_eigensolver", "exact", "classical"),
    "Q10": ("post_quantum_readiness_registry", "standards"),
}

ERROR = "error"
WARNING = "warning"
PASS = "pass"


def _json_load(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _new_id(prefix: str) -> str:
    return f"AGQ-{prefix}-{time.time_ns()}"


def _finding(
    code: str,
    status: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "status": status,
        "message": message,
        "details": details or {},
    }


def _report(
    gate_type: str,
    findings: list[dict[str, Any]],
    *,
    run_id: str | None = None,
    dataset_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    errors = [item for item in findings if item["status"] == ERROR]
    warnings = [item for item in findings if item["status"] == WARNING]
    status = "failed" if errors else ("warning" if warnings else "passed")
    return {
        "gate_type": gate_type,
        "status": status,
        "run_id": run_id,
        "dataset_id": dataset_id,
        "findings": findings,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "details": details or {},
    }


def _dataset_row(conn: sqlite3.Connection, dataset_id: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM quantum_datasets WHERE dataset_id=?",
        (dataset_id,),
    ).fetchone()
    if row is None:
        raise ValueError("Quantum dataset not found.")
    return row


def _dataset_for_runner(
    conn: sqlite3.Connection,
    dataset_id: str,
) -> dict[str, Any]:
    row = _dataset_row(conn, dataset_id)
    dataset = dict(row)
    dataset["source_tables"] = _json_load(
        dataset.pop("source_tables_json", None), []
    )
    dataset["source_record_ids"] = _json_load(
        dataset.pop("source_record_ids_json", None), {}
    )
    dataset["quality_summary"] = _json_load(
        dataset.pop("quality_summary_json", None), {}
    )
    dataset["permitted_families"] = _json_load(
        dataset.pop("permitted_families_json", None), []
    )
    dataset["snapshot"] = _json_load(
        dataset.pop("snapshot_json", None), {}
    )
    return dataset


def verify_dataset_integrity(
    conn: sqlite3.Connection,
    dataset_id: str,
) -> dict[str, Any]:
    row = _dataset_row(conn, dataset_id)
    findings: list[dict[str, Any]] = []

    try:
        snapshot = json.loads(row["snapshot_json"])
    except json.JSONDecodeError as exc:
        return _report(
            "dataset_integrity",
            [_finding(
                "DATASET_SNAPSHOT_JSON_INVALID",
                ERROR,
                "Frozen dataset snapshot JSON cannot be decoded.",
                {"error": str(exc)},
            )],
            dataset_id=dataset_id,
        )

    if not isinstance(snapshot, dict):
        return _report(
            "dataset_integrity",
            [_finding(
                "DATASET_SNAPSHOT_NOT_OBJECT",
                ERROR,
                "Frozen dataset snapshot must be a table-keyed object.",
            )],
            dataset_id=dataset_id,
        )

    recalculated = sha256_json(snapshot)
    findings.append(
        _finding(
            "DATASET_MANIFEST_MATCH"
            if recalculated == row["sha256"]
            else "DATASET_MANIFEST_MISMATCH",
            PASS if recalculated == row["sha256"] else ERROR,
            "Frozen dataset SHA-256 matches its canonical snapshot."
            if recalculated == row["sha256"]
            else "Frozen dataset SHA-256 does not match its stored snapshot.",
            {"expected": row["sha256"], "actual": recalculated},
        )
    )

    snapshot_records: dict[tuple[str, str], str] = {}
    record_count = 0
    for table, records in snapshot.items():
        if table not in DATASET_TABLES:
            findings.append(_finding(
                "DATASET_UNSUPPORTED_TABLE",
                ERROR,
                f"Frozen dataset contains unsupported table {table}.",
            ))
            continue
        if not isinstance(records, list):
            findings.append(_finding(
                "DATASET_TABLE_NOT_LIST",
                ERROR,
                f"Frozen dataset table {table} must contain a list.",
            ))
            continue
        primary_key = DATASET_TABLES[table]
        for record in records:
            if not isinstance(record, dict):
                findings.append(_finding(
                    "DATASET_RECORD_NOT_OBJECT",
                    ERROR,
                    f"Frozen dataset table {table} contains a non-object record.",
                ))
                continue
            record_id = str(record.get(primary_key, "")).strip()
            if not record_id:
                findings.append(_finding(
                    "DATASET_RECORD_ID_MISSING",
                    ERROR,
                    f"Frozen {table} record is missing {primary_key}.",
                ))
                continue
            snapshot_records[(table, record_id)] = sha256_json(record)
            record_count += 1

    findings.append(
        _finding(
            "DATASET_RECORD_COUNT_MATCH"
            if record_count == row["record_count"]
            else "DATASET_RECORD_COUNT_MISMATCH",
            PASS if record_count == row["record_count"] else ERROR,
            "Frozen record count matches the stored manifest."
            if record_count == row["record_count"]
            else "Frozen record count does not match the stored manifest.",
            {"expected": row["record_count"], "actual": record_count},
        )
    )

    lineage_rows = conn.execute(
        """SELECT source_table, source_record_id, payload_sha256
           FROM quantum_dataset_lineage WHERE dataset_id=?""",
        (dataset_id,),
    ).fetchall()
    lineage = {
        (item["source_table"], item["source_record_id"]): item["payload_sha256"]
        for item in lineage_rows
    }
    missing = sorted(set(snapshot_records) - set(lineage))
    extra = sorted(set(lineage) - set(snapshot_records))
    mismatched = sorted(
        key for key in set(snapshot_records) & set(lineage)
        if snapshot_records[key] != lineage[key]
    )
    lineage_ok = not (missing or extra or mismatched)
    findings.append(
        _finding(
            "DATASET_LINEAGE_MATCH"
            if lineage_ok else "DATASET_LINEAGE_MISMATCH",
            PASS if lineage_ok else ERROR,
            "Every frozen record matches its record-level SHA-256 lineage."
            if lineage_ok
            else "Frozen record lineage does not match the snapshot.",
            {
                "missing": [list(item) for item in missing],
                "extra": [list(item) for item in extra],
                "mismatched": [list(item) for item in mismatched],
            },
        )
    )

    source_drift: list[dict[str, str]] = []
    source_missing: list[dict[str, str]] = []
    for (table, record_id), frozen_digest in snapshot_records.items():
        primary_key = DATASET_TABLES[table]
        current = conn.execute(
            f"SELECT * FROM {table} WHERE {primary_key}=?",
            (record_id,),
        ).fetchone()
        if current is None:
            source_missing.append({"table": table, "record_id": record_id})
        elif sha256_json(dict(current)) != frozen_digest:
            source_drift.append({"table": table, "record_id": record_id})

    if source_drift or source_missing:
        findings.append(_finding(
            "SOURCE_DATA_DRIFT",
            WARNING,
            "Current AgroQ records differ from the frozen snapshot; frozen evidence remains immutable.",
            {"changed": source_drift, "missing": source_missing},
        ))
    else:
        findings.append(_finding(
            "SOURCE_DATA_UNCHANGED",
            PASS,
            "Current source records still match the frozen snapshot.",
        ))

    return _report(
        "dataset_integrity",
        findings,
        dataset_id=dataset_id,
        details={
            "stored_sha256": row["sha256"],
            "recalculated_sha256": recalculated,
            "record_count": record_count,
        },
    )


def _run_context(
    conn: sqlite3.Connection,
    run_id: str,
) -> tuple[sqlite3.Row, sqlite3.Row]:
    run = conn.execute(
        "SELECT * FROM quantum_runs WHERE run_id=?",
        (run_id,),
    ).fetchone()
    if run is None:
        raise ValueError("Quantum run not found.")
    experiment = conn.execute(
        "SELECT * FROM quantum_experiments WHERE experiment_id=?",
        (run["experiment_id"],),
    ).fetchone()
    if experiment is None:
        raise ValueError("Quantum experiment not found.")
    return run, experiment


def validate_classical_baseline(
    conn: sqlite3.Connection,
    run_id: str,
) -> dict[str, Any]:
    run, experiment = _run_context(conn, run_id)
    findings: list[dict[str, Any]] = []
    sequence = experiment["sequence"]
    run_type = experiment["run_type"]

    rows = conn.execute(
        """SELECT solver_name, feasible, constraint_violations, runtime_seconds
           FROM quantum_solver_results WHERE run_id=? ORDER BY solver_name""",
        (run_id,),
    ).fetchall()
    names = [str(row["solver_name"]) for row in rows]
    normalized = [name.lower().replace("-", "_") for name in names]
    exempt = sequence == "Q10" or run_type == "standards-registry"
    tokens = BASELINE_TOKENS.get(sequence, ("exact", "classical", "baseline"))
    present = exempt or any(
        any(token in solver_name for token in tokens)
        for solver_name in normalized
    )
    findings.append(_finding(
        "CLASSICAL_BASELINE_PRESENT" if present else "CLASSICAL_BASELINE_MISSING",
        PASS if present else ERROR,
        "A recognized classical or exact baseline is stored with the run."
        if present
        else "A recognized classical baseline is required before research approval.",
        {"solver_names": names, "exempt": exempt},
    ))

    controls = conn.execute(
        "SELECT * FROM quantum_claim_controls WHERE run_id=?",
        (run_id,),
    ).fetchone()
    matched = controls is not None and bool(controls["matched_budget"])
    findings.append(_finding(
        "MATCHED_BUDGET_DECLARED" if matched else "MATCHED_BUDGET_MISSING",
        PASS if matched else ERROR,
        "The run declares a matched solver budget."
        if matched
        else "Quantum and classical comparisons require a matched solver budget.",
    ))

    budget = _json_load(run["run_budget_json"], {})
    numeric = [
        value for value in budget.values()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    ]
    budget_ok = bool(budget) and (any(value > 0 for value in numeric) or exempt)
    findings.append(_finding(
        "RUN_BUDGET_RECORDED" if budget_ok else "RUN_BUDGET_INVALID",
        PASS if budget_ok else ERROR,
        "A valid run or evaluation budget is stored."
        if budget_ok
        else "A positive solver or evaluation budget is required.",
        {"run_budget": budget},
    ))

    runtime_ok = run["runtime_seconds"] is not None
    findings.append(_finding(
        "RUN_RUNTIME_RECORDED" if runtime_ok else "RUN_RUNTIME_MISSING",
        PASS if runtime_ok else ERROR,
        "Total run time is recorded."
        if runtime_ok else "Total run time must be recorded.",
        {"runtime_seconds": run["runtime_seconds"]},
    ))

    violations = [
        {
            "solver_name": row["solver_name"],
            "feasible": bool(row["feasible"]),
            "constraint_violations": row["constraint_violations"],
        }
        for row in rows
        if not bool(row["feasible"]) or int(row["constraint_violations"]) > 0
    ]
    findings.append(_finding(
        "SOLVER_RESULTS_FEASIBLE"
        if not violations else "SOLVER_CONSTRAINT_VIOLATIONS",
        PASS if not violations else ERROR,
        "Stored solver results report no constraint violations."
        if not violations
        else "One or more stored solver results violate the frozen constraints.",
        {"violations": violations},
    ))

    return _report(
        "classical_baseline",
        findings,
        run_id=run_id,
        dataset_id=experiment["dataset_id"],
        details={"sequence": sequence, "run_type": run_type},
    )


def replay_run(
    conn: sqlite3.Connection,
    run_id: str,
) -> dict[str, Any]:
    run, experiment = _run_context(conn, run_id)
    findings: list[dict[str, Any]] = []

    dataset = None
    if experiment["dataset_id"]:
        integrity = verify_dataset_integrity(conn, experiment["dataset_id"])
        if integrity["status"] == "failed":
            return _report(
                "deterministic_replay",
                [_finding(
                    "REPLAY_DATASET_INTEGRITY_FAILED",
                    ERROR,
                    "Deterministic replay was blocked because frozen dataset integrity failed.",
                    {"integrity": integrity},
                )],
                run_id=run_id,
                dataset_id=experiment["dataset_id"],
            )
        dataset = _dataset_for_runner(conn, experiment["dataset_id"])

    configuration = dict(_json_load(run["configuration_json"], {}))
    configuration["seed"] = int(run["seed"])
    execution = run_registered_experiment(
        experiment["sequence"],
        dataset=dataset,
        configuration=configuration,
    )
    actual = execution["result"]["result_sha256"]
    expected = run["result_sha256"]
    matched = bool(expected) and actual == expected
    findings.append(_finding(
        "DETERMINISTIC_REPLAY_MATCH"
        if matched else "DETERMINISTIC_REPLAY_MISMATCH",
        PASS if matched else ERROR,
        "The same dataset, configuration, and seed reproduced the stored result hash."
        if matched
        else "The replayed result hash differs from the stored result hash.",
        {"expected": expected, "actual": actual},
    ))
    return _report(
        "deterministic_replay",
        findings,
        run_id=run_id,
        dataset_id=experiment["dataset_id"],
        details={
            "configuration_sha256": sha256_json(configuration),
            "expected_result_sha256": expected,
            "replay_result_sha256": actual,
        },
    )


def evaluate_run_gates(
    conn: sqlite3.Connection,
    run_id: str,
    *,
    include_replay: bool = False,
) -> dict[str, Any]:
    run, experiment = _run_context(conn, run_id)
    findings: list[dict[str, Any]] = []

    completed = run["status"] == "completed"
    findings.append(_finding(
        "RUN_COMPLETED" if completed else "RUN_NOT_COMPLETED",
        PASS if completed else ERROR,
        "The run completed before scientific validation."
        if completed else "Only completed runs can pass scientific validation.",
        {"status": run["status"]},
    ))

    if experiment["dataset_id"]:
        integrity = verify_dataset_integrity(conn, experiment["dataset_id"])
        findings.extend(integrity["findings"])
    else:
        findings.append(_finding(
            "FROZEN_DATASET_MISSING",
            ERROR,
            "Research approval requires a persistent frozen dataset.",
        ))

    seed_ok = run["seed"] is not None
    findings.append(_finding(
        "SEED_RECORDED" if seed_ok else "SEED_MISSING",
        PASS if seed_ok else ERROR,
        "The run seed is recorded." if seed_ok else "A deterministic seed is required.",
        {"seed": run["seed"]},
    ))

    hash_ok = bool(run["result_sha256"])
    findings.append(_finding(
        "RESULT_HASH_RECORDED" if hash_ok else "RESULT_HASH_MISSING",
        PASS if hash_ok else ERROR,
        "The run result SHA-256 is recorded."
        if hash_ok else "A deterministic result SHA-256 is required.",
        {"result_sha256": run["result_sha256"]},
    ))

    findings.extend(validate_classical_baseline(conn, run_id)["findings"])

    controls = conn.execute(
        "SELECT * FROM quantum_claim_controls WHERE run_id=?",
        (run_id,),
    ).fetchone()
    if controls is None:
        findings.append(_finding(
            "CLAIM_CONTROLS_MISSING",
            ERROR,
            "Run claim controls are missing.",
        ))
    else:
        advantage = bool(controls["advantage_claim"])
        findings.append(_finding(
            "ADVANTAGE_CLAIM_PROHIBITED" if advantage else "NO_ADVANTAGE_CLAIM",
            ERROR if advantage else PASS,
            "Unsupported quantum-advantage claims are prohibited."
            if advantage else "No quantum-advantage claim is stored.",
        ))
        dependency = bool(controls["operational_dependency"])
        findings.append(_finding(
            "OPERATIONAL_DEPENDENCY_PROHIBITED"
            if dependency else "NO_OPERATIONAL_DEPENDENCY",
            ERROR if dependency else PASS,
            "Quantum execution cannot be an exclusive operational dependency."
            if dependency else "The run is not an exclusive operational dependency.",
        ))

        hardware_claimed = (
            bool(controls["hardware_used"])
            or experiment["run_type"] == "quantum-hardware"
        )
        if hardware_claimed:
            evidence = conn.execute(
                """SELECT COUNT(*) AS n FROM quantum_artifacts
                   WHERE run_id=? AND artifact_type='hardware_evidence'""",
                (run_id,),
            ).fetchone()["n"]
            configuration = _json_load(run["configuration_json"], {})
            metadata = (
                configuration.get("backend")
                or configuration.get("device")
                or configuration.get("hardware_backend")
            )
            findings.append(_finding(
                "HARDWARE_EVIDENCE_PRESENT"
                if evidence and metadata else "HARDWARE_EVIDENCE_MISSING",
                PASS if evidence and metadata else ERROR,
                "Hardware execution includes backend metadata and evidence."
                if evidence and metadata
                else "Hardware claims require backend metadata and a hardware-evidence artifact.",
            ))

    if include_replay:
        findings.extend(replay_run(conn, run_id)["findings"])

    return _report(
        "scientific_release",
        findings,
        run_id=run_id,
        dataset_id=experiment["dataset_id"],
        details={
            "experiment_id": experiment["experiment_id"],
            "sequence": experiment["sequence"],
            "include_replay": include_replay,
        },
    )


def record_validation_event(
    conn: sqlite3.Connection,
    report: dict[str, Any],
    *,
    user_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    validation_id = _new_id("QVALID")
    message = (
        f"{report['gate_type']} {report['status']}: "
        f"{report['error_count']} error(s), "
        f"{report['warning_count']} warning(s)."
    )
    conn.execute(
        """INSERT INTO quantum_validation_events(
            validation_id, run_id, dataset_id, gate_type, status,
            message, report_json, evaluated_by, created_at
        ) VALUES(?,?,?,?,?,?,?,?,?)""",
        (
            validation_id,
            report.get("run_id"),
            report.get("dataset_id"),
            report["gate_type"],
            report["status"],
            message,
            canonical_json(report),
            user_id,
            utc_now(),
        ),
    )
    return {"validation_id": validation_id, "message": message, **report}


def register_quantum_validation(
    *,
    app: Any,
    get_db: Callable[[], Any],
    utc_now: Callable[[], str],
    record_audit_event: Callable[..., None],
    roles_required: Callable[..., Any],
) -> None:
    from flask import Blueprint, g, jsonify, request

    blueprint = Blueprint("quantum_validation", __name__)

    @blueprint.get("/api/quantum/validation/summary")
    @roles_required(*Q14_VIEW_ROLES)
    def validation_summary() -> Response:
        with get_db() as conn:
            counts = {
                row["status"]: row["n"]
                for row in conn.execute(
                    """SELECT status, COUNT(*) AS n
                       FROM quantum_validation_events GROUP BY status"""
                ).fetchall()
            }
            rows = conn.execute(
                """SELECT validation_id, run_id, dataset_id, gate_type,
                          status, message, evaluated_by, created_at
                   FROM quantum_validation_events
                   ORDER BY created_at DESC LIMIT 50"""
            ).fetchall()
            runs = conn.execute(
                """SELECT r.run_id, r.experiment_id, e.sequence, e.title,
                          r.status, r.result_sha256, r.started_at
                   FROM quantum_runs r
                   JOIN quantum_experiments e
                     ON e.experiment_id=r.experiment_id
                   ORDER BY r.started_at DESC LIMIT 30"""
            ).fetchall()
            datasets = conn.execute(
                """SELECT dataset_id, name, sha256, record_count, created_at
                   FROM quantum_datasets
                   ORDER BY created_at DESC LIMIT 30"""
            ).fetchall()
        return jsonify({
            "ok": True,
            "schema_version": Q14_SCHEMA_VERSION,
            "counts": {
                "passed": counts.get("passed", 0),
                "warning": counts.get("warning", 0),
                "failed": counts.get("failed", 0),
            },
            "recent": [dict(row) for row in rows],
            "runs": [dict(row) for row in runs],
            "datasets": [dict(row) for row in datasets],
        })

    @blueprint.get("/api/quantum/runs/<run_id>/validation")
    @roles_required(*Q14_VIEW_ROLES)
    def run_validation_history(run_id: str) -> tuple[Response, int] | Response:
        with get_db() as conn:
            exists = conn.execute(
                "SELECT 1 FROM quantum_runs WHERE run_id=?",
                (run_id,),
            ).fetchone()
            if exists is None:
                return jsonify({"ok": False, "error": "Run not found"}), 404
            rows = conn.execute(
                """SELECT * FROM quantum_validation_events
                   WHERE run_id=? ORDER BY created_at DESC""",
                (run_id,),
            ).fetchall()
            events = []
            for row in rows:
                event = dict(row)
                event["report"] = _json_load(
                    event.pop("report_json", None), {}
                )
                events.append(event)
        return jsonify({"ok": True, "events": events})

    @blueprint.post("/api/quantum/datasets/<dataset_id>/verify")
    @roles_required(*Q14_EXECUTE_ROLES)
    def verify_dataset(dataset_id: str) -> tuple[Response, int] | Response:
        try:
            with get_db() as conn:
                report = verify_dataset_integrity(conn, dataset_id)
                event = record_validation_event(
                    conn,
                    report,
                    user_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 404
        record_audit_event(
            g.user["user_id"],
            "quantum_dataset_integrity_checked",
            "quantum_dataset",
            dataset_id,
            canonical_json({"status": event["status"]}),
        )
        return jsonify({"ok": True, "validation": event})

    @blueprint.post("/api/quantum/runs/<run_id>/validate")
    @roles_required(*Q14_EXECUTE_ROLES)
    def validate_run(run_id: str) -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        include_replay = bool(payload.get("include_replay", False))
        try:
            with get_db() as conn:
                report = evaluate_run_gates(
                    conn, run_id, include_replay=include_replay
                )
                event = record_validation_event(
                    conn,
                    report,
                    user_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 404
        record_audit_event(
            g.user["user_id"],
            "quantum_run_validated",
            "quantum_run",
            run_id,
            canonical_json({"status": event["status"]}),
        )
        return jsonify({"ok": True, "validation": event})

    @blueprint.post("/api/quantum/runs/<run_id>/replay")
    @roles_required(*Q14_EXECUTE_ROLES)
    def replay_quantum_run(run_id: str) -> tuple[Response, int] | Response:
        try:
            with get_db() as conn:
                report = replay_run(conn, run_id)
                event = record_validation_event(
                    conn,
                    report,
                    user_id=g.user["user_id"],
                    utc_now=utc_now,
                )
                conn.execute(
                    """INSERT INTO quantum_replay_checks(
                        replay_id, run_id, expected_result_sha256,
                        replay_result_sha256, deterministic,
                        configuration_sha256, created_by, created_at
                    ) VALUES(?,?,?,?,?,?,?,?)""",
                    (
                        _new_id("QREPLAY"),
                        run_id,
                        report["details"].get("expected_result_sha256"),
                        report["details"].get("replay_result_sha256"),
                        1 if report["status"] == "passed" else 0,
                        report["details"].get("configuration_sha256"),
                        g.user["user_id"],
                        utc_now(),
                    ),
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 404
        record_audit_event(
            g.user["user_id"],
            "quantum_run_replayed",
            "quantum_run",
            run_id,
            canonical_json({"status": event["status"]}),
        )
        return jsonify({"ok": True, "validation": event})

    app.register_blueprint(blueprint)
