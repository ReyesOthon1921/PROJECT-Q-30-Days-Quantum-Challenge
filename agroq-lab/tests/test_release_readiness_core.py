import sqlite3

from release_readiness import collect_release_readiness


def make_connection(with_backup=True, failed_validation=False):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE backup_runs(
            backup_id TEXT,
            filename TEXT,
            status TEXT,
            size_bytes INTEGER,
            verification_message TEXT,
            created_at TEXT,
            verified_at TEXT
        );
        CREATE TABLE quantum_validation_events(
            validation_id TEXT,
            run_id TEXT,
            gate_type TEXT,
            status TEXT,
            message TEXT,
            created_at TEXT
        );
        CREATE TABLE quantum_research_operations(
            lifecycle_state TEXT,
            released_at TEXT
        );
        CREATE TABLE quantum_evidence_bundles(id TEXT);
        """
    )
    if with_backup:
        conn.execute(
            """INSERT INTO backup_runs VALUES(
                'B1','backup.sqlite3','verified',100,'ok',
                '2026-01-01','2026-01-01'
            )"""
        )
    if failed_validation:
        conn.execute(
            """INSERT INTO quantum_validation_events VALUES(
                'V1','R1','scientific_release','failed',
                'failed gate','2026-01-01'
            )"""
        )
    return conn


def gateway():
    return {
        "deployment_ready": True,
        "secret_configured": True,
        "database_engine": "sqlite",
        "database_path": "/tmp/agroq.db",
        "deployment_mode": "staging",
        "bind_host": "0.0.0.0",
        "debug_enabled": False,
        "safety_issues": [],
    }


def test_release_readiness_passes_with_backup_and_safe_runtime(monkeypatch):
    monkeypatch.setenv("WEB_CONCURRENCY", "1")
    payload = collect_release_readiness(
        make_connection(),
        gateway=gateway(),
    )
    assert payload["ready"] is True


def test_release_readiness_blocks_failed_scientific_gate(monkeypatch):
    monkeypatch.setenv("WEB_CONCURRENCY", "1")
    payload = collect_release_readiness(
        make_connection(failed_validation=True),
        gateway=gateway(),
    )
    assert payload["ready"] is False
    failed = {
        item["code"]
        for item in payload["checks"]
        if not item["passed"]
    }
    assert "SCIENTIFIC_GATES" in failed


def test_release_readiness_blocks_missing_backup(monkeypatch):
    monkeypatch.setenv("WEB_CONCURRENCY", "1")
    payload = collect_release_readiness(
        make_connection(with_backup=False),
        gateway=gateway(),
    )
    assert payload["ready"] is False
    assert any(
        item["code"] == "VERIFIED_BACKUP" and not item["passed"]
        for item in payload["checks"]
    )
