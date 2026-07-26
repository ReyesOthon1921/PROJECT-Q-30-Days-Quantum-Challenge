from quantum_validation import verify_dataset_integrity
from test_quantum_validation_core import make_connection, seed_dataset


def test_record_level_lineage_tampering_is_detected():
    conn = make_connection()
    seed_dataset(conn)
    conn.execute(
        """UPDATE quantum_dataset_lineage
           SET payload_sha256='sha256:tampered'
           WHERE dataset_id='D-1'"""
    )
    report = verify_dataset_integrity(conn, "D-1")
    assert report["status"] == "failed"
    assert "DATASET_LINEAGE_MISMATCH" in {
        item["code"] for item in report["findings"]
    }


def test_current_source_drift_warns_without_mutating_frozen_snapshot():
    conn = make_connection()
    seed_dataset(conn)
    before = conn.execute(
        "SELECT snapshot_json FROM quantum_datasets WHERE dataset_id='D-1'"
    ).fetchone()["snapshot_json"]
    conn.execute("UPDATE plots SET name='Changed current source' WHERE plot_id='P-1'")
    report = verify_dataset_integrity(conn, "D-1")
    after = conn.execute(
        "SELECT snapshot_json FROM quantum_datasets WHERE dataset_id='D-1'"
    ).fetchone()["snapshot_json"]
    assert report["status"] == "warning"
    assert before == after
    assert "SOURCE_DATA_DRIFT" in {
        item["code"] for item in report["findings"]
    }


def test_record_count_tampering_is_detected():
    conn = make_connection()
    seed_dataset(conn)
    conn.execute(
        "UPDATE quantum_datasets SET record_count=99 WHERE dataset_id='D-1'"
    )
    report = verify_dataset_integrity(conn, "D-1")
    assert report["status"] == "failed"
    assert "DATASET_RECORD_COUNT_MISMATCH" in {
        item["code"] for item in report["findings"]
    }
