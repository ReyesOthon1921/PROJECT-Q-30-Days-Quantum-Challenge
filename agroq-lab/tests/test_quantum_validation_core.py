import sqlite3

from quantum_runner import canonical_json, run_registered_experiment, sha256_json
from quantum_validation import (
    _dataset_for_runner,
    evaluate_run_gates,
    replay_run,
    validate_classical_baseline,
    verify_dataset_integrity,
)


def make_connection():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
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
        """
    )
    return conn


def seed_dataset(conn):
    plot = {
        "plot_id": "P-1",
        "name": "North",
        "plot_type": "control",
        "area": "0.1 acre",
        "status": "Active",
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    conn.execute("INSERT INTO plots VALUES(?,?,?,?,?,?)", tuple(plot.values()))
    snapshot = {"plots": [plot]}
    conn.execute(
        """INSERT INTO quantum_datasets VALUES(
            'D-1','Frozen','agroq_database_snapshot',?,?,?,?,?,?,?,?,?,?
        )""",
        (
            canonical_json(["plots"]),
            canonical_json({"plots": ["P-1"]}),
            canonical_json(snapshot),
            sha256_json(snapshot),
            1,
            canonical_json({}),
            canonical_json(["Q10"]),
            "U-1",
            "2026-01-01T00:00:00+00:00",
            "pending",
        ),
    )
    conn.execute(
        "INSERT INTO quantum_dataset_lineage VALUES(?,?,?,?)",
        ("D-1", "plots", "P-1", sha256_json(plot)),
    )


def seed_run(conn):
    seed_dataset(conn)
    config = {"seed": 301, "inventory": []}
    dataset = _dataset_for_runner(conn, "D-1")
    result = run_registered_experiment(
        "Q10", dataset=dataset, configuration=config
    )["result"]
    conn.execute(
        """INSERT INTO quantum_experiments VALUES(
            'E-1','Q10','Registry','Security','[]','Registered',
            'standards-registry','Registry','D-1','{}','hash','commit',
            '{}','','{}','U-1','now','now'
        )"""
    )
    conn.execute(
        """INSERT INTO quantum_runs VALUES(
            'R-1','E-1','Registry','standards-registry',301,?,
            ?,'completed','now','now',0.1,?,NULL,'U-1'
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
        """INSERT INTO quantum_claim_controls VALUES(
            'R-1',1,0,0,0,1,0,0,1
        )"""
    )


def test_dataset_integrity_passes_and_detects_snapshot_tampering():
    conn = make_connection()
    seed_dataset(conn)
    assert verify_dataset_integrity(conn, "D-1")["status"] == "passed"

    conn.execute(
        "UPDATE quantum_datasets SET snapshot_json=? WHERE dataset_id='D-1'",
        (canonical_json({"plots": []}),),
    )
    report = verify_dataset_integrity(conn, "D-1")
    assert report["status"] == "failed"
    assert "DATASET_MANIFEST_MISMATCH" in {
        item["code"] for item in report["findings"]
    }


def test_same_seed_and_configuration_reproduce_result_hash():
    conn = make_connection()
    seed_run(conn)
    report = replay_run(conn, "R-1")
    assert report["status"] == "passed"
    assert (
        report["details"]["expected_result_sha256"]
        == report["details"]["replay_result_sha256"]
    )


def test_complete_registry_run_passes_baseline_and_release_gates():
    conn = make_connection()
    seed_run(conn)
    assert validate_classical_baseline(conn, "R-1")["status"] == "passed"
    assert evaluate_run_gates(
        conn, "R-1", include_replay=True
    )["status"] == "passed"


def test_unsafe_claim_and_missing_baseline_are_blocked():
    conn = make_connection()
    seed_run(conn)
    conn.execute(
        "UPDATE quantum_claim_controls SET advantage_claim=1 WHERE run_id='R-1'"
    )
    conn.execute("DELETE FROM quantum_solver_results WHERE run_id='R-1'")
    conn.execute(
        """UPDATE quantum_experiments
           SET sequence='Q2', run_type='quantum-simulator'
           WHERE experiment_id='E-1'"""
    )
    report = evaluate_run_gates(conn, "R-1")
    assert report["status"] == "failed"
    codes = {item["code"] for item in report["findings"]}
    assert "ADVANTAGE_CLAIM_PROHIBITED" in codes
    assert "CLASSICAL_BASELINE_MISSING" in codes
