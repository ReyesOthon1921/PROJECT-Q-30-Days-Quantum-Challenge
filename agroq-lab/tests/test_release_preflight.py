import json
import sqlite3
from pathlib import Path

from release_manifest import build_manifest
from release_preflight import (
    REQUIRED_TABLES,
    latest_failed_validation_count,
    parse_render_worker_count,
    release_operation_blocker_count,
    schema_check,
    secret_check,
    storage_check,
    worker_configuration_check,
)


def test_parse_render_worker_count():
    text = """
services:
  - type: web
    envVars:
      - key: WEB_CONCURRENCY
        value: "1"
"""
    assert parse_render_worker_count(text) == 1


def test_worker_configuration_requires_one_sqlite_worker(tmp_path):
    (tmp_path / "agroq-lab").mkdir()
    (tmp_path / "render.yaml").write_text(
        """
services:
  - type: web
    envVars:
      - key: WEB_CONCURRENCY
        value: "1"
""",
        encoding="utf-8",
    )
    (tmp_path / "agroq-lab" / "Dockerfile").write_text(
        'CMD ["sh", "-c", "gunicorn --workers ${WEB_CONCURRENCY:-1} wsgi:app"]\n',
        encoding="utf-8",
    )
    assert worker_configuration_check(tmp_path).passed is True

    (tmp_path / "render.yaml").write_text(
        """
services:
  - type: web
    envVars:
      - key: WEB_CONCURRENCY
        value: "2"
""",
        encoding="utf-8",
    )
    assert worker_configuration_check(tmp_path).passed is False


def test_storage_check_creates_writable_directories(tmp_path):
    result = storage_check(
        tmp_path / "instance" / "agroq.db",
        tmp_path / "backups",
    )
    assert result.passed is True


def test_schema_check_requires_all_q16_tables(tmp_path):
    schema_path = tmp_path / "schema.sql"
    statements = [
        f"CREATE TABLE IF NOT EXISTS {table}(id TEXT);"
        for table in sorted(REQUIRED_TABLES)
    ]
    schema_path.write_text("\n".join(statements), encoding="utf-8")
    result = schema_check(
        schema_path,
        tmp_path / "instance" / "agroq.db",
    )
    assert result.passed is True
    assert result.details["integrity"] == "ok"
    assert result.details["missing_tables"] == []


def test_latest_failed_validation_uses_latest_event():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """CREATE TABLE quantum_validation_events(
            validation_id TEXT,
            run_id TEXT,
            gate_type TEXT,
            status TEXT,
            created_at TEXT
        )"""
    )
    conn.executemany(
        "INSERT INTO quantum_validation_events VALUES(?,?,?,?,?)",
        [
            ("V1", "R1", "scientific_release", "failed", "2026-01-01"),
            ("V2", "R1", "scientific_release", "passed", "2026-01-02"),
            ("V3", "R2", "deterministic_replay", "failed", "2026-01-03"),
        ],
    )
    assert latest_failed_validation_count(conn) == 1


def test_release_operation_blocker_count():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """CREATE TABLE quantum_research_operations(
            lifecycle_state TEXT,
            released_at TEXT
        )"""
    )
    conn.executemany(
        "INSERT INTO quantum_research_operations VALUES(?,?)",
        [
            ("Approved for research", None),
            ("Released", "2026-01-01"),
        ],
    )
    assert release_operation_blocker_count(conn) == 1


def test_secret_check_rejects_defaults_and_accepts_safe_values(monkeypatch):
    monkeypatch.delenv("AGROQ_SECRET_KEY", raising=False)
    monkeypatch.delenv("AGROQ_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("AGROQ_DEPLOYMENT_MODE", raising=False)
    assert secret_check().passed is False

    monkeypatch.setenv(
        "AGROQ_SECRET_KEY",
        "q16-test-secret-value-long-enough",
    )
    monkeypatch.setenv(
        "AGROQ_ADMIN_PASSWORD",
        "q16-test-password-long-enough",
    )
    monkeypatch.setenv("AGROQ_DEPLOYMENT_MODE", "staging")
    monkeypatch.setenv("AGROQ_DEBUG", "false")
    assert secret_check().passed is True


def test_release_manifest_records_critical_files(tmp_path, monkeypatch):
    for relative in (
        "render.yaml",
        "agroq-lab/Dockerfile",
        "agroq-lab/app.py",
        "agroq-lab/schema.sql",
        "agroq-lab/release_preflight.py",
        "agroq-lab/release_manifest.py",
        "agroq-lab/staging_smoke.py",
        "agroq-lab/release_readiness.py",
        ".github/workflows/agroq-q16-validation.yml",
        "agroq-lab/docs/Q16_RELEASE_RUNBOOK.md",
        "agroq-lab/docs/Q16_ROLLBACK_RUNBOOK.md",
        "agroq-lab/docs/RESEARCH_MENTORS_AND_COLLABORATORS.md",
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative, encoding="utf-8")

    monkeypatch.setattr(
        "release_manifest.git_value",
        lambda *_args, **_kwargs: "test",
    )
    manifest = build_manifest(tmp_path)
    assert manifest["ready"] is True
    assert manifest["missing_files"] == []
    assert len(manifest["critical_files"]) == 12
