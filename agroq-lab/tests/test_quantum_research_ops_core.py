import io
import json
import sqlite3
import zipfile
from pathlib import Path

import pytest

from quantum_research_ops import (
    build_evidence_bundle,
    create_research_operation,
    ensure_run_operation,
    record_release_checklist,
    store_evidence_bundle,
    transition_research_operation,
)
from quantum_runner import canonical_json, run_registered_experiment, sha256_json


def utc_now():
    return "2026-07-25T12:00:00+00:00"


def make_connection():
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
        CREATE TABLE plots(
            plot_id TEXT PRIMARY KEY,
            name TEXT,
            plot_type TEXT,
            area TEXT,
            status TEXT,
            created_at TEXT
        );
        CREATE TABLE quantum_datasets(
            dataset_id TEXT PRIMARY KEY,
            name TEXT,
            source_kind TEXT,
            source_tables_json TEXT,
            source_record_ids_json TEXT,
            snapshot_json TEXT,
            sha256 TEXT,
            record_count INTEGER,
            quality_summary_json TEXT,
            permitted_families_json TEXT,
            created_by TEXT,
            created_at TEXT,
            review_status TEXT
        );
        CREATE TABLE quantum_dataset_lineage(
            dataset_id TEXT,
            source_table TEXT,
            source_record_id TEXT,
            payload_sha256 TEXT,
            PRIMARY KEY(dataset_id, source_table, source_record_id)
        );
        CREATE TABLE quantum_experiments(
            experiment_id TEXT PRIMARY KEY,
            sequence TEXT,
            title TEXT,
            problem_family TEXT,
            source_ids_json TEXT,
            status TEXT,
            run_type TEXT,
            algorithm TEXT,
            dataset_id TEXT,
            formulation_json TEXT,
            formulation_sha256 TEXT,
            code_commit TEXT,
            claim_controls_json TEXT,
            notes TEXT,
            raw_record_json TEXT,
            created_by TEXT,
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE quantum_runs(
            run_id TEXT PRIMARY KEY,
            experiment_id TEXT,
            algorithm TEXT,
            run_type TEXT,
            seed INTEGER,
            run_budget_json TEXT,
            configuration_json TEXT,
            status TEXT,
            started_at TEXT,
            completed_at TEXT,
            runtime_seconds REAL,
            result_sha256 TEXT,
            error_message TEXT,
            created_by TEXT
        );
        CREATE TABLE quantum_solver_results(
            result_id TEXT PRIMARY KEY,
            run_id TEXT,
            solver_name TEXT,
            result_json TEXT,
            objective REAL,
            feasible INTEGER,
            constraint_violations INTEGER,
            approximation_gap REAL,
            runtime_seconds REAL
        );
        CREATE TABLE quantum_artifacts(
            artifact_id TEXT PRIMARY KEY,
            run_id TEXT,
            artifact_type TEXT,
            filename TEXT,
            media_type TEXT,
            content_text TEXT,
            sha256 TEXT,
            created_at TEXT
        );
        CREATE TABLE quantum_reviews(
            review_id TEXT PRIMARY KEY,
            run_id TEXT,
            decision TEXT,
            notes TEXT,
            reviewer_id TEXT,
            reviewed_at TEXT
        );
        CREATE TABLE quantum_claim_controls(
            run_id TEXT PRIMARY KEY,
            simulator_only INTEGER,
            hardware_used INTEGER,
            advantage_claim INTEGER,
            operational_dependency INTEGER,
            matched_budget INTEGER,
            classical_baseline_required INTEGER,
            synthetic_data INTEGER,
            human_review_required INTEGER
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
        CREATE TABLE quantum_replay_checks(
            replay_id TEXT PRIMARY KEY,
            run_id TEXT,
            expected_result_sha256 TEXT,
            replay_result_sha256 TEXT,
            deterministic INTEGER,
            configuration_sha256 TEXT,
            created_by TEXT,
            created_at TEXT
        );
        """
    )
    schema = Path(__file__).resolve().parents[1] / "quantum_research_ops_schema.sql"
    conn.executescript(schema.read_text(encoding="utf-8"))
    return conn


def seed_complete_run(conn):
    users = [
        ("U-RESEARCH", "research", "Researcher", "x", "researcher", "S", 1, "now"),
        ("U-ADMIN", "admin", "Administrator", "x", "administrator", "S", 1, "now"),
        ("U-ADMIN2", "admin2", "Reviewer", "x", "administrator", "S", 1, "now"),
    ]
    conn.executemany("INSERT INTO users VALUES(?,?,?,?,?,?,?,?)", users)

    plot = {
        "plot_id": "P-1",
        "name": "North",
        "plot_type": "control",
        "area": "0.1 acre",
        "status": "Active",
        "created_at": "now",
    }
    conn.execute("INSERT INTO plots VALUES(?,?,?,?,?,?)", tuple(plot.values()))
    snapshot = {"plots": [plot]}
    dataset_sha = sha256_json(snapshot)
    conn.execute(
        """INSERT INTO quantum_datasets VALUES(
            'D-1','Frozen','agroq_database_snapshot',?,?,?,?,?,?,?,?,?,?
        )""",
        (
            canonical_json(["plots"]),
            canonical_json({"plots": ["P-1"]}),
            canonical_json(snapshot),
            dataset_sha,
            1,
            canonical_json({}),
            canonical_json(["Q10"]),
            "U-RESEARCH",
            "now",
            "approved",
        ),
    )
    conn.execute(
        "INSERT INTO quantum_dataset_lineage VALUES(?,?,?,?)",
        ("D-1", "plots", "P-1", sha256_json(plot)),
    )
    config = {"seed": 301, "inventory": []}
    dataset = {
        "dataset_id": "D-1",
        "sha256": dataset_sha,
        "snapshot": snapshot,
    }
    result = run_registered_experiment(
        "Q10",
        dataset=dataset,
        configuration=config,
    )["result"]
    conn.execute(
        """INSERT INTO quantum_experiments VALUES(
            'E-1','Q10','Security registry','Security','[]','Registered',
            'standards-registry','Registry','D-1','{}','hash','commit-1',
            '{}','','{}','U-RESEARCH','now','now'
        )"""
    )
    conn.execute(
        """INSERT INTO quantum_runs VALUES(
            'R-1','E-1','Registry','standards-registry',301,?,
            ?,'completed','now','now',0.05,?,NULL,'U-RESEARCH'
        )""",
        (
            canonical_json({"registry_checks": 1}),
            canonical_json(config),
            result["result_sha256"],
        ),
    )
    conn.execute(
        """INSERT INTO quantum_solver_results VALUES(
            'S-1','R-1','post_quantum_readiness_registry','{}',
            NULL,1,0,NULL,0.01
        )"""
    )
    conn.execute(
        """INSERT INTO quantum_artifacts VALUES(
            'A-1','R-1','result_json','result.json',
            'application/json','{}',?,'now'
        )""",
        (sha256_json({}),),
    )
    conn.execute(
        """INSERT INTO quantum_claim_controls VALUES(
            'R-1',1,0,0,0,1,0,0,1
        )"""
    )


def approve_operation(conn):
    operation = ensure_run_operation(
        conn,
        "R-1",
        actor_id="U-RESEARCH",
        utc_now=utc_now,
    )
    operation = transition_research_operation(
        conn,
        operation["operation_id"],
        {
            "to_state": "Under review",
            "reason": "Research run completed.",
            "research_notes": "Compared the registry against the frozen inputs.",
            "limitations": "Standards registry only; no cryptographic implementation.",
        },
        actor_id="U-RESEARCH",
        actor_role="researcher",
        utc_now=utc_now,
    )
    return transition_research_operation(
        conn,
        operation["operation_id"],
        {
            "to_state": "Approved for research",
            "reason": "Independent administrator review passed.",
            "research_notes": operation["research_notes"],
            "limitations": operation["limitations"],
        },
        actor_id="U-ADMIN",
        actor_role="administrator",
        utc_now=utc_now,
    )


def test_researcher_cannot_approve_own_run():
    conn = make_connection()
    seed_complete_run(conn)
    operation = ensure_run_operation(
        conn, "R-1", actor_id="U-RESEARCH", utc_now=utc_now
    )
    operation = transition_research_operation(
        conn,
        operation["operation_id"],
        {
            "to_state": "Under review",
            "reason": "Ready for independent review.",
            "research_notes": "Research notes.",
            "limitations": "Known limitations.",
        },
        actor_id="U-RESEARCH",
        actor_role="researcher",
        utc_now=utc_now,
    )
    with pytest.raises(PermissionError):
        transition_research_operation(
            conn,
            operation["operation_id"],
            {
                "to_state": "Approved for research",
                "reason": "Self approval.",
                "research_notes": "Research notes.",
                "limitations": "Known limitations.",
            },
            actor_id="U-RESEARCH",
            actor_role="administrator",
            utc_now=utc_now,
        )


def test_independent_approval_records_replay_and_validation():
    conn = make_connection()
    seed_complete_run(conn)
    operation = approve_operation(conn)
    assert operation["lifecycle_state"] == "Approved for research"
    assert operation["reviewer_id"] == "U-ADMIN"
    gate_types = {
        row["gate_type"]
        for row in conn.execute(
            "SELECT gate_type FROM quantum_validation_events"
        ).fetchall()
    }
    assert {"deterministic_replay", "scientific_release"} <= gate_types


def test_evidence_bundle_contains_required_files_and_hashes():
    conn = make_connection()
    seed_complete_run(conn)
    operation = approve_operation(conn)
    bundle, manifest = store_evidence_bundle(
        conn,
        operation["operation_id"],
        actor_id="U-ADMIN",
        utc_now=utc_now,
    )
    assert manifest["bundle_sha256"]
    with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
        names = set(archive.namelist())
        required = {
            "experiment.json",
            "dataset_manifest.json",
            "lineage_records.json",
            "configuration.json",
            "solver_results.json",
            "review_history.json",
            "claim_controls.json",
            "validation_history.json",
            "research_operation.json",
            "environment.json",
            "failed_run_diagnostics.json",
            "README.md",
            "SHA256SUMS.txt",
            "artifacts/result.json",
        }
        assert required <= names
        sums = archive.read("SHA256SUMS.txt").decode("utf-8")
        assert "experiment.json" in sums
        assert "solver_results.json" in sums


def test_release_requires_complete_manual_checklist_and_evidence():
    conn = make_connection()
    seed_complete_run(conn)
    operation = approve_operation(conn)

    with pytest.raises(ValueError):
        transition_research_operation(
            conn,
            operation["operation_id"],
            {
                "to_state": "Released",
                "reason": "Too early.",
                "research_notes": operation["research_notes"],
                "limitations": operation["limitations"],
            },
            actor_id="U-ADMIN2",
            actor_role="administrator",
            utc_now=utc_now,
        )

    store_evidence_bundle(
        conn,
        operation["operation_id"],
        actor_id="U-ADMIN",
        utc_now=utc_now,
    )
    checklist = record_release_checklist(
        conn,
        operation["operation_id"],
        {
            "manual": {
                "limitations_disclosed": True,
                "evidence_reviewed": True,
                "rollback_plan_documented": True,
                "release_notes_complete": True,
            }
        },
        actor_id="U-ADMIN",
        actor_role="administrator",
        utc_now=utc_now,
    )
    assert checklist["complete"] is True
    released = transition_research_operation(
        conn,
        operation["operation_id"],
        {
            "to_state": "Released",
            "reason": "Complete evidence and release review.",
            "research_notes": operation["research_notes"],
            "limitations": operation["limitations"],
        },
        actor_id="U-ADMIN2",
        actor_role="administrator",
        utc_now=utc_now,
    )
    assert released["lifecycle_state"] == "Released"


def test_lifecycle_history_is_immutable():
    conn = make_connection()
    seed_complete_run(conn)
    operation = ensure_run_operation(
        conn, "R-1", actor_id="U-RESEARCH", utc_now=utc_now
    )
    event_id = operation["history"][0]["event_id"]
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "UPDATE quantum_lifecycle_events SET reason='changed' WHERE event_id=?",
            (event_id,),
        )

def test_rejected_operation_and_history_remain_preserved():
    conn = make_connection()
    seed_complete_run(conn)
    operation = ensure_run_operation(
        conn, "R-1", actor_id="U-RESEARCH", utc_now=utc_now
    )
    operation = transition_research_operation(
        conn,
        operation["operation_id"],
        {
            "to_state": "Under review",
            "reason": "Review requested.",
            "research_notes": "Research notes.",
            "limitations": "Known limitations.",
        },
        actor_id="U-RESEARCH",
        actor_role="researcher",
        utc_now=utc_now,
    )
    rejected = transition_research_operation(
        conn,
        operation["operation_id"],
        {
            "to_state": "Rejected",
            "reason": "Evidence requires revision.",
            "research_notes": "Research notes.",
            "limitations": "Known limitations.",
        },
        actor_id="U-ADMIN",
        actor_role="administrator",
        utc_now=utc_now,
    )
    assert rejected["lifecycle_state"] == "Rejected"
    assert [event["to_state"] for event in rejected["history"]] == [
        "Completed",
        "Under review",
        "Rejected",
    ]


def test_superseded_operation_links_replacement_without_deleting_old_run():
    conn = make_connection()
    seed_complete_run(conn)
    old = ensure_run_operation(
        conn, "R-1", actor_id="U-RESEARCH", utc_now=utc_now
    )
    replacement = create_research_operation(
        conn,
        {
            "experiment_id": "E-1",
            "research_notes": "Replacement research plan.",
            "limitations": "Pending new run.",
        },
        actor_id="U-RESEARCH",
        actor_role="researcher",
        utc_now=utc_now,
    )
    superseded = transition_research_operation(
        conn,
        old["operation_id"],
        {
            "to_state": "Superseded",
            "reason": "A replacement research operation was opened.",
            "replacement_operation_id": replacement["operation_id"],
        },
        actor_id="U-RESEARCH",
        actor_role="researcher",
        utc_now=utc_now,
    )
    assert superseded["lifecycle_state"] == "Superseded"
    assert superseded["superseded_by_operation_id"] == replacement["operation_id"]
    replacement_row = conn.execute(
        """SELECT supersedes_operation_id
           FROM quantum_research_operations
           WHERE operation_id=?""",
        (replacement["operation_id"],),
    ).fetchone()
    assert replacement_row["supersedes_operation_id"] == old["operation_id"]
    assert conn.execute(
        "SELECT 1 FROM quantum_runs WHERE run_id='R-1'"
    ).fetchone() is not None

def test_evidence_bundle_is_deterministic_for_unchanged_records():
    conn = make_connection()
    seed_complete_run(conn)
    operation = approve_operation(conn)
    first, first_manifest = build_evidence_bundle(
        conn, operation["operation_id"]
    )
    second, second_manifest = build_evidence_bundle(
        conn, operation["operation_id"]
    )
    assert first == second
    assert first_manifest["bundle_sha256"] == second_manifest["bundle_sha256"]
