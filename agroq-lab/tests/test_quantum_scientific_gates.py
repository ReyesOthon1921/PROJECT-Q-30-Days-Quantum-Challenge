from quantum_validation import evaluate_run_gates
from test_quantum_validation_core import make_connection, seed_run


def gate_codes(report):
    return {finding["code"] for finding in report["findings"]}


def test_missing_frozen_dataset_blocks_approval_gate():
    conn = make_connection()
    seed_run(conn)
    conn.execute(
        "UPDATE quantum_experiments SET dataset_id=NULL WHERE experiment_id='E-1'"
    )
    report = evaluate_run_gates(conn, "R-1")
    assert report["status"] == "failed"
    assert "FROZEN_DATASET_MISSING" in gate_codes(report)


def test_missing_seed_and_budget_block_approval_gate():
    conn = make_connection()
    seed_run(conn)
    conn.execute(
        """UPDATE quantum_runs
           SET seed=NULL, run_budget_json='{}'
           WHERE run_id='R-1'"""
    )
    report = evaluate_run_gates(conn, "R-1")
    assert report["status"] == "failed"
    assert {"SEED_MISSING", "RUN_BUDGET_INVALID"} <= gate_codes(report)


def test_operational_dependency_blocks_approval_gate():
    conn = make_connection()
    seed_run(conn)
    conn.execute(
        """UPDATE quantum_claim_controls
           SET operational_dependency=1
           WHERE run_id='R-1'"""
    )
    report = evaluate_run_gates(conn, "R-1")
    assert report["status"] == "failed"
    assert "OPERATIONAL_DEPENDENCY_PROHIBITED" in gate_codes(report)


def test_hardware_claim_without_evidence_is_blocked():
    conn = make_connection()
    seed_run(conn)
    conn.execute(
        """UPDATE quantum_experiments
           SET run_type='quantum-hardware'
           WHERE experiment_id='E-1'"""
    )
    conn.execute(
        """UPDATE quantum_claim_controls
           SET hardware_used=1
           WHERE run_id='R-1'"""
    )
    report = evaluate_run_gates(conn, "R-1")
    assert report["status"] == "failed"
    assert "HARDWARE_EVIDENCE_MISSING" in gate_codes(report)
