from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Callable

from flask import Blueprint, Response, g, jsonify, request

from quantum_runner import (
    SUPPORTED_SEQUENCES,
    canonical_json,
    run_registered_experiment,
    sha256_json,
    sha256_text,
)


QUANTUM_VIEW_ROLES = ("administrator", "researcher", "field_operator", "viewer")
QUANTUM_EDIT_ROLES = ("administrator", "researcher")
QUANTUM_REVIEW_ROLES = ("administrator", "researcher")
MAX_QUANTUM_PAYLOAD_BYTES = 2_000_000

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

EXPERIMENT_STATUSES = frozenset(
    {
        "Planned",
        "Registered",
        "Ready for baseline",
        "Simulation complete",
        "Registry complete",
        "Archived",
    }
)
RUN_TYPES = frozenset(
    {
        "classical",
        "quantum-inspired",
        "quantum-simulator",
        "quantum-hardware",
        "standards-registry",
    }
)
REVIEW_DECISIONS = frozenset(
    {"approved_for_research", "rejected", "needs_revision"}
)


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return None if row is None else dict(row)


def _json_load(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _bounded_json_request() -> dict[str, Any]:
    if request.content_length and request.content_length > MAX_QUANTUM_PAYLOAD_BYTES:
        raise ValueError(
            f"Quantum API payload exceeds {MAX_QUANTUM_PAYLOAD_BYTES} bytes."
        )
    payload = request.get_json(silent=True)
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValueError("JSON request body must be an object.")
    return payload


def _new_id(prefix: str) -> str:
    return f"AGQ-{prefix}-{time.time_ns()}"


def seed_quantum_sources(
    conn: sqlite3.Connection,
    source_path: Path,
    utc_now: Callable[[], str],
) -> int:
    if not source_path.is_file():
        return 0
    source_payload = json.loads(source_path.read_text(encoding="utf-8"))
    if not isinstance(source_payload, list):
        raise ValueError("Quantum source seed must contain a JSON list.")

    existing_count = conn.execute(
        "SELECT COUNT(*) AS n FROM quantum_research_sources"
    ).fetchone()["n"]
    if existing_count == len(source_payload):
        return 0

    count = 0
    now = utc_now()
    for source in source_payload:
        if not isinstance(source, dict):
            continue
        source_id = str(source.get("id", "")).strip()
        title = str(source.get("title", "")).strip()
        if not source_id or not title:
            continue
        conn.execute(
            """INSERT INTO quantum_research_sources(
                source_id, sequence_json, title, authors_json, year, venue,
                publication_status, identifier, url, mechanism, agroq_feature,
                reproduction_target, evidence_status, limitations,
                acknowledgment, endorsement_boundary, tags_json, created_at,
                updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(source_id) DO UPDATE SET
                sequence_json=excluded.sequence_json,
                title=excluded.title,
                authors_json=excluded.authors_json,
                year=excluded.year,
                venue=excluded.venue,
                publication_status=excluded.publication_status,
                identifier=excluded.identifier,
                url=excluded.url,
                mechanism=excluded.mechanism,
                agroq_feature=excluded.agroq_feature,
                reproduction_target=excluded.reproduction_target,
                evidence_status=excluded.evidence_status,
                limitations=excluded.limitations,
                acknowledgment=excluded.acknowledgment,
                endorsement_boundary=excluded.endorsement_boundary,
                tags_json=excluded.tags_json,
                updated_at=excluded.updated_at
            """,
            (
                source_id,
                canonical_json(source.get("sequence", [])),
                title,
                canonical_json(source.get("authors", [])),
                source.get("year"),
                source.get("venue"),
                source.get("publicationStatus"),
                source.get("identifier"),
                source.get("url"),
                source.get("mechanism"),
                source.get("agroqFeature"),
                source.get("reproductionTarget"),
                source.get("evidenceStatus"),
                source.get("limitations"),
                source.get("acknowledgment"),
                source.get("endorsementBoundary"),
                canonical_json(source.get("tags", [])),
                now,
                now,
            ),
        )
        count += 1
    return count


def _serialize_source(row: sqlite3.Row) -> dict[str, Any]:
    source = dict(row)
    source["sequence"] = _json_load(source.pop("sequence_json", None), [])
    source["authors"] = _json_load(source.pop("authors_json", None), [])
    source["tags"] = _json_load(source.pop("tags_json", None), [])
    return source


def _serialize_dataset(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    include_snapshot: bool = False,
) -> dict[str, Any]:
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
    if include_snapshot:
        dataset["snapshot"] = _json_load(
            dataset.pop("snapshot_json", None), {}
        )
        lineage_rows = conn.execute(
            """SELECT source_table, source_record_id, payload_sha256
               FROM quantum_dataset_lineage
               WHERE dataset_id=?
               ORDER BY source_table, source_record_id""",
            (dataset["dataset_id"],),
        ).fetchall()
        dataset["lineage"] = [dict(item) for item in lineage_rows]
    else:
        dataset.pop("snapshot_json", None)
    return dataset


def _serialize_experiment(row: sqlite3.Row) -> dict[str, Any]:
    experiment = dict(row)
    for key in (
        "source_ids_json",
        "formulation_json",
        "claim_controls_json",
        "raw_record_json",
    ):
        output_key = key.removesuffix("_json")
        experiment[output_key] = _json_load(experiment.pop(key, None), None)
    return experiment


def _serialize_run(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    include_details: bool = True,
) -> dict[str, Any]:
    run = dict(row)
    for key in ("run_budget_json", "configuration_json"):
        run[key.removesuffix("_json")] = _json_load(run.pop(key, None), {})
    if not include_details:
        return run

    results = conn.execute(
        """SELECT * FROM quantum_solver_results
           WHERE run_id=? ORDER BY solver_name""",
        (run["run_id"],),
    ).fetchall()
    run["solver_results"] = []
    for item in results:
        payload = dict(item)
        payload["result"] = _json_load(payload.pop("result_json", None), {})
        run["solver_results"].append(payload)

    artifacts = conn.execute(
        """SELECT artifact_id, run_id, artifact_type, filename, media_type,
                  sha256, created_at
           FROM quantum_artifacts WHERE run_id=? ORDER BY created_at""",
        (run["run_id"],),
    ).fetchall()
    run["artifacts"] = [dict(item) for item in artifacts]

    reviews = conn.execute(
        """SELECT r.*, u.display_name AS reviewer_name
           FROM quantum_reviews r
           JOIN users u ON u.user_id=r.reviewer_id
           WHERE r.run_id=? ORDER BY reviewed_at DESC""",
        (run["run_id"],),
    ).fetchall()
    run["reviews"] = [dict(item) for item in reviews]

    controls = conn.execute(
        "SELECT * FROM quantum_claim_controls WHERE run_id=?",
        (run["run_id"],),
    ).fetchone()
    run["claim_controls"] = dict(controls) if controls else None
    return run


def _dataset_quality_summary(snapshot: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    observation_rows = snapshot.get("observations", [])
    quality_counts: dict[str, int] = {}
    missing_values = 0

    for row in observation_rows:
        flag = str(row.get("quality_flag") or "unknown")
        quality_counts[flag] = quality_counts.get(flag, 0) + 1
        if row.get("value") is None:
            missing_values += 1

    return {
        "table_record_counts": {
            table: len(rows) for table, rows in snapshot.items()
        },
        "observation_quality_flags": quality_counts,
        "missing_observation_values": missing_values,
        "lineage_record_count": sum(len(rows) for rows in snapshot.values()),
    }


def _freeze_dataset(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    user_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    name = str(payload.get("name", "")).strip()
    if not name:
        raise ValueError("Dataset name is required.")

    requested_tables = payload.get("source_tables")
    if not isinstance(requested_tables, list) or not requested_tables:
        raise ValueError("Choose at least one supported source table.")

    source_tables: list[str] = []
    for table in requested_tables:
        normalized = str(table).strip()
        if normalized not in DATASET_TABLES:
            raise ValueError(f"Unsupported source table: {normalized}")
        if normalized not in source_tables:
            source_tables.append(normalized)

    record_filters = payload.get("record_ids") or {}
    if not isinstance(record_filters, dict):
        raise ValueError("record_ids must be an object keyed by source table.")

    snapshot: dict[str, list[dict[str, Any]]] = {}
    source_record_ids: dict[str, list[str]] = {}
    lineage: list[tuple[str, str, str]] = []

    for table in source_tables:
        primary_key = DATASET_TABLES[table]
        requested_ids = record_filters.get(table)
        if requested_ids is not None:
            if not isinstance(requested_ids, list):
                raise ValueError(f"record_ids.{table} must be a list.")
            normalized_ids = [
                str(value).strip() for value in requested_ids if str(value).strip()
            ]
        else:
            normalized_ids = []

        if normalized_ids:
            if len(normalized_ids) > 500:
                raise ValueError(f"Too many IDs requested for {table}.")
            placeholders = ",".join("?" for _ in normalized_ids)
            rows = conn.execute(
                f"""SELECT * FROM {table}
                    WHERE {primary_key} IN ({placeholders})
                    ORDER BY {primary_key}""",
                tuple(normalized_ids),
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT * FROM {table} ORDER BY {primary_key} LIMIT 500"
            ).fetchall()

        serialized = [dict(row) for row in rows]
        snapshot[table] = serialized
        source_record_ids[table] = [
            str(row[primary_key]) for row in serialized
        ]
        for row in serialized:
            row_id = str(row[primary_key])
            lineage.append((table, row_id, sha256_json(row)))

    if not any(snapshot.values()):
        raise ValueError("The selected source tables produced no records.")

    permitted = payload.get("permitted_families") or sorted(SUPPORTED_SEQUENCES)
    if not isinstance(permitted, list):
        raise ValueError("permitted_families must be a list.")
    normalized_permitted = []
    for sequence in permitted:
        normalized = str(sequence).upper().strip()
        if normalized not in SUPPORTED_SEQUENCES:
            raise ValueError(f"Unsupported permitted experiment family: {normalized}")
        if normalized not in normalized_permitted:
            normalized_permitted.append(normalized)

    dataset_id = str(payload.get("dataset_id") or _new_id("QDATA")).strip()
    snapshot_json = canonical_json(snapshot)
    dataset_sha256 = sha256_text(snapshot_json)
    quality_summary = _dataset_quality_summary(snapshot)
    created_at = utc_now()

    existing = conn.execute(
        "SELECT * FROM quantum_datasets WHERE sha256=?",
        (dataset_sha256,),
    ).fetchone()
    if existing is not None:
        return _serialize_dataset(conn, existing, include_snapshot=True)

    conn.execute(
        """INSERT INTO quantum_datasets(
            dataset_id, name, source_kind, source_tables_json,
            source_record_ids_json, snapshot_json, sha256, record_count,
            quality_summary_json, permitted_families_json, created_by,
            created_at, review_status
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            dataset_id,
            name,
            "agroq_database_snapshot",
            canonical_json(source_tables),
            canonical_json(source_record_ids),
            snapshot_json,
            dataset_sha256,
            sum(len(rows) for rows in snapshot.values()),
            canonical_json(quality_summary),
            canonical_json(normalized_permitted),
            user_id,
            created_at,
            "pending",
        ),
    )
    conn.executemany(
        """INSERT INTO quantum_dataset_lineage(
            dataset_id, source_table, source_record_id, payload_sha256
        ) VALUES(?,?,?,?)""",
        [
            (dataset_id, table, record_id, digest)
            for table, record_id, digest in lineage
        ],
    )
    row = conn.execute(
        "SELECT * FROM quantum_datasets WHERE dataset_id=?",
        (dataset_id,),
    ).fetchone()
    assert row is not None
    return _serialize_dataset(conn, row, include_snapshot=True)


def _validate_experiment_payload(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
) -> dict[str, Any]:
    experiment_id = str(
        payload.get("experimentId")
        or payload.get("experiment_id")
        or _new_id("QEXP")
    ).strip()
    sequence = str(payload.get("sequence", "")).upper().strip()
    if sequence not in SUPPORTED_SEQUENCES:
        raise ValueError(
            f"sequence must be one of: {', '.join(sorted(SUPPORTED_SEQUENCES))}."
        )

    title = str(payload.get("title", "")).strip()
    if not title:
        raise ValueError("Experiment title is required.")

    source_ids = payload.get("sourceIds")
    if source_ids is None:
        source_ids = payload.get("source_ids")
    if not isinstance(source_ids, list) or not source_ids:
        raise ValueError("At least one source ID is required.")
    normalized_source_ids = []
    for source_id in source_ids:
        normalized = str(source_id).strip()
        exists = conn.execute(
            "SELECT 1 FROM quantum_research_sources WHERE source_id=?",
            (normalized,),
        ).fetchone()
        if exists is None:
            raise ValueError(f"Unknown quantum research source: {normalized}")
        if normalized not in normalized_source_ids:
            normalized_source_ids.append(normalized)

    status = str(payload.get("status", "Registered")).strip()
    if status not in EXPERIMENT_STATUSES:
        raise ValueError("Experiment status is invalid.")

    run_type = str(
        payload.get("runType") or payload.get("run_type") or "quantum-simulator"
    ).strip()
    if run_type not in RUN_TYPES:
        raise ValueError("Experiment run type is invalid.")

    dataset_payload = payload.get("dataset")
    explicit_dataset_id = payload.get("dataset_id")
    dataset_id = explicit_dataset_id
    if dataset_id is None and isinstance(dataset_payload, dict):
        candidate_id = dataset_payload.get("id") or dataset_payload.get("dataset_id")
        if candidate_id:
            exists = conn.execute(
                "SELECT 1 FROM quantum_datasets WHERE dataset_id=?",
                (str(candidate_id).strip(),),
            ).fetchone()
            if exists is not None:
                dataset_id = candidate_id
    dataset_id = str(dataset_id).strip() if dataset_id else None
    if dataset_id:
        dataset = conn.execute(
            "SELECT permitted_families_json FROM quantum_datasets WHERE dataset_id=?",
            (dataset_id,),
        ).fetchone()
        if dataset is None:
            raise ValueError("Linked quantum dataset does not exist.")
        permitted = _json_load(dataset["permitted_families_json"], [])
        if sequence not in permitted:
            raise ValueError(
                f"Dataset {dataset_id} does not permit sequence {sequence}."
            )

    formulation = payload.get("formulation")
    if not isinstance(formulation, dict):
        formulation = {}
    claim_controls = payload.get("claimControls")
    if not isinstance(claim_controls, dict):
        claim_controls = payload.get("claim_controls")
    if not isinstance(claim_controls, dict):
        claim_controls = {}

    if bool(claim_controls.get("advantageClaim")) or bool(
        claim_controls.get("advantage_claim")
    ):
        raise ValueError(
            "Advantage claims require a later independent review workflow."
        )
    if bool(claim_controls.get("operationalDependency")) or bool(
        claim_controls.get("operational_dependency")
    ):
        raise ValueError(
            "Quantum experiments cannot be an exclusive operational dependency."
        )

    formulation_hash = (
        formulation.get("hash")
        or formulation.get("sha256")
        or sha256_json(formulation)
    )
    return {
        "experiment_id": experiment_id,
        "sequence": sequence,
        "title": title,
        "problem_family": str(
            payload.get("problemFamily")
            or payload.get("problem_family")
            or title
        ).strip(),
        "source_ids": normalized_source_ids,
        "status": status,
        "run_type": run_type,
        "algorithm": str(payload.get("algorithm", "")).strip() or None,
        "dataset_id": dataset_id,
        "formulation": formulation,
        "formulation_sha256": formulation_hash,
        "code_commit": str(
            payload.get("codeCommit") or payload.get("code_commit") or "unknown"
        ).strip(),
        "claim_controls": claim_controls,
        "notes": str(payload.get("notes", "")).strip(),
        "raw_record": payload,
    }


def _store_experiment(
    conn: sqlite3.Connection,
    normalized: dict[str, Any],
    *,
    user_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    now = utc_now()
    conn.execute(
        """INSERT INTO quantum_experiments(
            experiment_id, sequence, title, problem_family, source_ids_json,
            status, run_type, algorithm, dataset_id, formulation_json,
            formulation_sha256, code_commit, claim_controls_json, notes,
            raw_record_json, created_by, created_at, updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(experiment_id) DO UPDATE SET
            title=excluded.title,
            problem_family=excluded.problem_family,
            source_ids_json=excluded.source_ids_json,
            status=excluded.status,
            run_type=excluded.run_type,
            algorithm=excluded.algorithm,
            dataset_id=excluded.dataset_id,
            formulation_json=excluded.formulation_json,
            formulation_sha256=excluded.formulation_sha256,
            code_commit=excluded.code_commit,
            claim_controls_json=excluded.claim_controls_json,
            notes=excluded.notes,
            raw_record_json=excluded.raw_record_json,
            updated_at=excluded.updated_at
        """,
        (
            normalized["experiment_id"],
            normalized["sequence"],
            normalized["title"],
            normalized["problem_family"],
            canonical_json(normalized["source_ids"]),
            normalized["status"],
            normalized["run_type"],
            normalized["algorithm"],
            normalized["dataset_id"],
            canonical_json(normalized["formulation"]),
            normalized["formulation_sha256"],
            normalized["code_commit"],
            canonical_json(normalized["claim_controls"]),
            normalized["notes"],
            canonical_json(normalized["raw_record"]),
            user_id,
            now,
            now,
        ),
    )
    row = conn.execute(
        "SELECT * FROM quantum_experiments WHERE experiment_id=?",
        (normalized["experiment_id"],),
    ).fetchone()
    assert row is not None
    return _serialize_experiment(row)


def _dataset_for_runner(
    conn: sqlite3.Connection,
    dataset_id: str | None,
) -> dict[str, Any] | None:
    if not dataset_id:
        return None
    row = conn.execute(
        "SELECT * FROM quantum_datasets WHERE dataset_id=?",
        (dataset_id,),
    ).fetchone()
    if row is None:
        raise ValueError("Linked dataset no longer exists.")
    return _serialize_dataset(conn, row, include_snapshot=True)


def _create_run(
    conn: sqlite3.Connection,
    experiment: sqlite3.Row,
    payload: dict[str, Any],
    *,
    user_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    run_id = str(payload.get("run_id") or _new_id("QRUN")).strip()
    configuration = payload.get("configuration")
    if not isinstance(configuration, dict):
        configuration = {}
    seed = int(configuration.get("seed", payload.get("seed", 301)))
    run_budget = payload.get("run_budget")
    if not isinstance(run_budget, dict):
        run_budget = {
            "solution_samples": int(configuration.get("run_budget", 2048)),
            "matched_across_solvers": True,
        }

    started_at = utc_now()
    conn.execute(
        """INSERT INTO quantum_runs(
            run_id, experiment_id, algorithm, run_type, seed,
            run_budget_json, configuration_json, status, started_at,
            created_by
        ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (
            run_id,
            experiment["experiment_id"],
            experiment["algorithm"],
            experiment["run_type"],
            seed,
            canonical_json(run_budget),
            canonical_json(configuration),
            "running",
            started_at,
            user_id,
        ),
    )

    dataset = _dataset_for_runner(conn, experiment["dataset_id"])
    try:
        execution = run_registered_experiment(
            experiment["sequence"],
            dataset=dataset,
            configuration=configuration,
        )
    except Exception as exc:
        completed_at = utc_now()
        conn.execute(
            """UPDATE quantum_runs
               SET status='failed', completed_at=?, error_message=?
               WHERE run_id=?""",
            (completed_at, str(exc), run_id),
        )
        raise

    result = execution["result"]
    result_sha256 = result["result_sha256"]
    completed_at = utc_now()
    conn.execute(
        """UPDATE quantum_runs
           SET status='completed', completed_at=?, runtime_seconds=?,
               result_sha256=?
           WHERE run_id=?""",
        (
            completed_at,
            execution["runtime_seconds"],
            result_sha256,
            run_id,
        ),
    )

    for item in result.get("solver_results", []):
        solver_name = str(item.get("solver_name", "unknown"))
        solver_result = item.get("result")
        if not isinstance(solver_result, dict):
            solver_result = {"value": solver_result}
        best = solver_result.get("best")
        metrics = solver_result.get("metrics", {})
        objective = None
        feasible = True
        violations = 0
        approximation_gap = None
        runtime_seconds = solver_result.get("runtime_seconds")

        if isinstance(best, dict):
            objective = best.get("energy")
            feasible = bool(best.get("feasible", True))
            violations = int(best.get("constraint_violations", 0))
        elif isinstance(metrics, dict):
            objective = metrics.get("rmse", metrics.get("accuracy"))

        result_id = _new_id("QRESULT")
        conn.execute(
            """INSERT INTO quantum_solver_results(
                result_id, run_id, solver_name, result_json, objective,
                feasible, constraint_violations, approximation_gap,
                runtime_seconds
            ) VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                result_id,
                run_id,
                solver_name,
                canonical_json(solver_result),
                objective,
                1 if feasible else 0,
                violations,
                approximation_gap,
                runtime_seconds,
            ),
        )

    for artifact in execution["artifacts"]:
        content_text = str(artifact["content_text"])
        conn.execute(
            """INSERT INTO quantum_artifacts(
                artifact_id, run_id, artifact_type, filename, media_type,
                content_text, sha256, created_at
            ) VALUES(?,?,?,?,?,?,?,?)""",
            (
                _new_id("QART"),
                run_id,
                artifact["artifact_type"],
                artifact["filename"],
                artifact["media_type"],
                content_text,
                sha256_text(content_text),
                completed_at,
            ),
        )

    controls = result.get("controls") or {}
    conn.execute(
        """INSERT INTO quantum_claim_controls(
            run_id, simulator_only, hardware_used, advantage_claim,
            operational_dependency, matched_budget,
            classical_baseline_required, synthetic_data,
            human_review_required
        ) VALUES(?,?,?,?,?,?,?,?,?)""",
        (
            run_id,
            1 if controls.get("simulator_only", True) else 0,
            1 if controls.get("hardware_used", False) else 0,
            1 if controls.get("advantage_claim", False) else 0,
            1 if controls.get("operational_dependency", False) else 0,
            1 if controls.get("matched_budget", True) else 0,
            1 if controls.get("classical_baseline_required", True) else 0,
            1 if controls.get("synthetic_data", dataset is None) else 0,
            1 if controls.get("human_review_required", True) else 0,
        ),
    )

    row = conn.execute(
        "SELECT * FROM quantum_runs WHERE run_id=?",
        (run_id,),
    ).fetchone()
    assert row is not None
    return _serialize_run(conn, row)


def register_quantum_backend(
    *,
    app: Any,
    get_db: Callable[[], Any],
    utc_now: Callable[[], str],
    record_audit_event: Callable[..., None],
    roles_required: Callable[..., Any],
    source_seed_path: Path,
) -> None:
    blueprint = Blueprint("quantum_backend", __name__)

    def ensure_sources(conn: sqlite3.Connection) -> None:
        seed_quantum_sources(conn, source_seed_path, utc_now)

    @blueprint.get("/api/quantum/health")
    @roles_required(*QUANTUM_VIEW_ROLES)
    def quantum_health() -> Response:
        with get_db() as conn:
            ensure_sources(conn)
            counts = {
                "sources": conn.execute(
                    "SELECT COUNT(*) AS n FROM quantum_research_sources"
                ).fetchone()["n"],
                "datasets": conn.execute(
                    "SELECT COUNT(*) AS n FROM quantum_datasets"
                ).fetchone()["n"],
                "experiments": conn.execute(
                    "SELECT COUNT(*) AS n FROM quantum_experiments"
                ).fetchone()["n"],
                "runs": conn.execute(
                    "SELECT COUNT(*) AS n FROM quantum_runs"
                ).fetchone()["n"],
            }
        return jsonify(
            {
                "ok": True,
                "service": "AgroQ Quantum Backend",
                "schema_version": "AGROQ-QBACKEND-1.0",
                "supported_sequences": sorted(SUPPORTED_SEQUENCES),
                "counts": counts,
            }
        )

    @blueprint.get("/api/quantum/sources")
    @roles_required(*QUANTUM_VIEW_ROLES)
    def list_quantum_sources() -> Response:
        with get_db() as conn:
            ensure_sources(conn)
            rows = conn.execute(
                """SELECT * FROM quantum_research_sources
                   ORDER BY source_id"""
            ).fetchall()
        return jsonify(
            {
                "ok": True,
                "sources": [_serialize_source(row) for row in rows],
            }
        )

    @blueprint.get("/api/quantum/datasets")
    @roles_required(*QUANTUM_VIEW_ROLES)
    def list_quantum_datasets() -> Response:
        with get_db() as conn:
            rows = conn.execute(
                """SELECT * FROM quantum_datasets
                   ORDER BY created_at DESC"""
            ).fetchall()
            datasets = [
                _serialize_dataset(conn, row, include_snapshot=False)
                for row in rows
            ]
        return jsonify({"ok": True, "datasets": datasets})

    @blueprint.post("/api/quantum/datasets/freeze")
    @roles_required(*QUANTUM_EDIT_ROLES)
    def freeze_quantum_dataset() -> tuple[Response, int] | Response:
        try:
            payload = _bounded_json_request()
            with get_db() as conn:
                dataset = _freeze_dataset(
                    conn,
                    payload,
                    user_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except (ValueError, sqlite3.IntegrityError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

        record_audit_event(
            g.user["user_id"],
            "quantum_dataset_frozen",
            "quantum_dataset",
            dataset["dataset_id"],
            canonical_json(
                {
                    "sha256": dataset["sha256"],
                    "record_count": dataset["record_count"],
                    "source_tables": dataset["source_tables"],
                }
            ),
        )
        return jsonify({"ok": True, "dataset": dataset}), 201

    @blueprint.get("/api/quantum/datasets/<dataset_id>")
    @roles_required(*QUANTUM_VIEW_ROLES)
    def quantum_dataset_detail(dataset_id: str) -> tuple[Response, int] | Response:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM quantum_datasets WHERE dataset_id=?",
                (dataset_id,),
            ).fetchone()
            if row is None:
                return jsonify({"ok": False, "error": "Dataset not found"}), 404
            dataset = _serialize_dataset(conn, row, include_snapshot=True)
        return jsonify({"ok": True, "dataset": dataset})

    @blueprint.get("/api/quantum/experiments")
    @roles_required(*QUANTUM_VIEW_ROLES)
    def list_quantum_experiments() -> Response:
        with get_db() as conn:
            ensure_sources(conn)
            rows = conn.execute(
                """SELECT * FROM quantum_experiments
                   ORDER BY updated_at DESC"""
            ).fetchall()
        return jsonify(
            {
                "ok": True,
                "experiments": [_serialize_experiment(row) for row in rows],
            }
        )

    @blueprint.post("/api/quantum/experiments")
    @roles_required(*QUANTUM_EDIT_ROLES)
    def create_quantum_experiment() -> tuple[Response, int] | Response:
        try:
            payload = _bounded_json_request()
            with get_db() as conn:
                ensure_sources(conn)
                normalized = _validate_experiment_payload(conn, payload)
                experiment = _store_experiment(
                    conn,
                    normalized,
                    user_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except (ValueError, sqlite3.IntegrityError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

        record_audit_event(
            g.user["user_id"],
            "quantum_experiment_registered",
            "quantum_experiment",
            experiment["experiment_id"],
            canonical_json(
                {
                    "sequence": experiment["sequence"],
                    "dataset_id": experiment["dataset_id"],
                }
            ),
        )
        return jsonify({"ok": True, "experiment": experiment}), 201

    @blueprint.get("/api/quantum/experiments/<experiment_id>")
    @roles_required(*QUANTUM_VIEW_ROLES)
    def quantum_experiment_detail(
        experiment_id: str,
    ) -> tuple[Response, int] | Response:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM quantum_experiments WHERE experiment_id=?",
                (experiment_id,),
            ).fetchone()
            if row is None:
                return jsonify(
                    {"ok": False, "error": "Experiment not found"}
                ), 404
            runs = conn.execute(
                """SELECT * FROM quantum_runs
                   WHERE experiment_id=? ORDER BY started_at DESC""",
                (experiment_id,),
            ).fetchall()
            experiment = _serialize_experiment(row)
            experiment["runs"] = [
                _serialize_run(conn, run, include_details=False)
                for run in runs
            ]
        return jsonify({"ok": True, "experiment": experiment})

    @blueprint.post("/api/quantum/experiments/<experiment_id>/dataset")
    @roles_required(*QUANTUM_EDIT_ROLES)
    def attach_quantum_dataset(
        experiment_id: str,
    ) -> tuple[Response, int] | Response:
        try:
            payload = _bounded_json_request()
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        dataset_id = str(payload.get("dataset_id", "")).strip()
        if not dataset_id:
            return jsonify(
                {"ok": False, "error": "dataset_id is required."}
            ), 400

        with get_db() as conn:
            experiment = conn.execute(
                "SELECT * FROM quantum_experiments WHERE experiment_id=?",
                (experiment_id,),
            ).fetchone()
            if experiment is None:
                return jsonify(
                    {"ok": False, "error": "Experiment not found"}
                ), 404
            dataset = conn.execute(
                "SELECT * FROM quantum_datasets WHERE dataset_id=?",
                (dataset_id,),
            ).fetchone()
            if dataset is None:
                return jsonify(
                    {"ok": False, "error": "Dataset not found"}
                ), 404
            permitted = _json_load(
                dataset["permitted_families_json"], []
            )
            if experiment["sequence"] not in permitted:
                return jsonify(
                    {
                        "ok": False,
                        "error": (
                            f"Dataset {dataset_id} does not permit "
                            f"{experiment['sequence']}."
                        ),
                    }
                ), 400
            conn.execute(
                """UPDATE quantum_experiments
                   SET dataset_id=?, updated_at=?
                   WHERE experiment_id=?""",
                (dataset_id, utc_now(), experiment_id),
            )
            updated = conn.execute(
                "SELECT * FROM quantum_experiments WHERE experiment_id=?",
                (experiment_id,),
            ).fetchone()
            assert updated is not None
            serialized = _serialize_experiment(updated)

        record_audit_event(
            g.user["user_id"],
            "quantum_dataset_attached",
            "quantum_experiment",
            experiment_id,
            canonical_json({"dataset_id": dataset_id}),
        )
        return jsonify({"ok": True, "experiment": serialized})

    @blueprint.post("/api/quantum/experiments/<experiment_id>/runs")
    @roles_required(*QUANTUM_EDIT_ROLES)
    def run_quantum_experiment(
        experiment_id: str,
    ) -> tuple[Response, int] | Response:
        try:
            payload = _bounded_json_request()
            with get_db() as conn:
                experiment = conn.execute(
                    "SELECT * FROM quantum_experiments WHERE experiment_id=?",
                    (experiment_id,),
                ).fetchone()
                if experiment is None:
                    return jsonify(
                        {"ok": False, "error": "Experiment not found"}
                    ), 404
                run = _create_run(
                    conn,
                    experiment,
                    payload,
                    user_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        except Exception as exc:
            app.logger.exception("Quantum server run failed.")
            return jsonify({"ok": False, "error": str(exc)}), 500

        record_audit_event(
            g.user["user_id"],
            "quantum_run_completed",
            "quantum_run",
            run["run_id"],
            canonical_json(
                {
                    "experiment_id": experiment_id,
                    "status": run["status"],
                    "result_sha256": run["result_sha256"],
                }
            ),
        )
        return jsonify({"ok": True, "run": run}), 201

    @blueprint.get("/api/quantum/runs/<run_id>")
    @roles_required(*QUANTUM_VIEW_ROLES)
    def quantum_run_detail(run_id: str) -> tuple[Response, int] | Response:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM quantum_runs WHERE run_id=?",
                (run_id,),
            ).fetchone()
            if row is None:
                return jsonify({"ok": False, "error": "Run not found"}), 404
            run = _serialize_run(conn, row)
        return jsonify({"ok": True, "run": run})

    @blueprint.post("/api/quantum/runs/<run_id>/review")
    @roles_required(*QUANTUM_REVIEW_ROLES)
    def review_quantum_run(run_id: str) -> tuple[Response, int] | Response:
        try:
            payload = _bounded_json_request()
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        decision = str(payload.get("decision", "")).strip()
        notes = str(payload.get("notes", "")).strip()
        if decision not in REVIEW_DECISIONS or not notes:
            return jsonify(
                {
                    "ok": False,
                    "error": "A valid decision and review notes are required.",
                }
            ), 400

        with get_db() as conn:
            run = conn.execute(
                "SELECT * FROM quantum_runs WHERE run_id=?",
                (run_id,),
            ).fetchone()
            if run is None:
                return jsonify({"ok": False, "error": "Run not found"}), 404
            review_id = _new_id("QREVIEW")
            conn.execute(
                """INSERT INTO quantum_reviews(
                    review_id, run_id, decision, notes, reviewer_id,
                    reviewed_at
                ) VALUES(?,?,?,?,?,?)""",
                (
                    review_id,
                    run_id,
                    decision,
                    notes,
                    g.user["user_id"],
                    utc_now(),
                ),
            )
            row = conn.execute(
                "SELECT * FROM quantum_reviews WHERE review_id=?",
                (review_id,),
            ).fetchone()
            assert row is not None
            review = dict(row)

        record_audit_event(
            g.user["user_id"],
            "quantum_run_reviewed",
            "quantum_review",
            review_id,
            canonical_json({"run_id": run_id, "decision": decision}),
        )
        return jsonify({"ok": True, "review": review}), 201

    @blueprint.get("/api/quantum/runs/<run_id>/artifacts")
    @roles_required(*QUANTUM_VIEW_ROLES)
    def list_quantum_artifacts(run_id: str) -> tuple[Response, int] | Response:
        with get_db() as conn:
            exists = conn.execute(
                "SELECT 1 FROM quantum_runs WHERE run_id=?",
                (run_id,),
            ).fetchone()
            if exists is None:
                return jsonify({"ok": False, "error": "Run not found"}), 404
            rows = conn.execute(
                """SELECT artifact_id, run_id, artifact_type, filename,
                          media_type, sha256, created_at
                   FROM quantum_artifacts WHERE run_id=?
                   ORDER BY created_at""",
                (run_id,),
            ).fetchall()
        return jsonify(
            {"ok": True, "artifacts": [dict(row) for row in rows]}
        )

    @blueprint.get("/api/quantum/artifacts/<artifact_id>")
    @roles_required(*QUANTUM_VIEW_ROLES)
    def download_quantum_artifact(
        artifact_id: str,
    ) -> tuple[Response, int] | Response:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM quantum_artifacts WHERE artifact_id=?",
                (artifact_id,),
            ).fetchone()
        if row is None:
            return jsonify({"ok": False, "error": "Artifact not found"}), 404
        response = Response(
            row["content_text"],
            content_type=row["media_type"],
        )
        response.headers["Content-Disposition"] = (
            f'attachment; filename="{row["filename"]}"'
        )
        response.headers["X-AgroQ-SHA256"] = row["sha256"]
        return response

    app.register_blueprint(blueprint)
