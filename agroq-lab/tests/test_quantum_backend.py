import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

_INITIAL_TEST_ROOT = Path(tempfile.mkdtemp(prefix="agroq-q11-q13-tests-"))
_INITIAL_TEST_DB = _INITIAL_TEST_ROOT / "test_quantum_backend.db"
_INITIAL_BACKUP_DIR = _INITIAL_TEST_ROOT / "backups"
_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema.sql"

with sqlite3.connect(_INITIAL_TEST_DB) as _initial_conn:
    _initial_conn.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))

os.environ["AGROQ_DB_PATH"] = str(_INITIAL_TEST_DB)
os.environ.setdefault("AGROQ_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("AGROQ_ADMIN_USERNAME", "testadmin")
os.environ.setdefault("AGROQ_ADMIN_PASSWORD", "test-password-123")
os.environ["AGROQ_BACKUP_DIR"] = str(_INITIAL_BACKUP_DIR)

import app as app_module  # noqa: E402
from app import app, get_db, init_db  # noqa: E402


@pytest.fixture(autouse=True)
def clean_quantum_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_quantum_backend.db"
    backup_path = tmp_path / "backups"
    monkeypatch.setenv("AGROQ_DB_PATH", str(db_path))
    monkeypatch.setenv("AGROQ_BACKUP_DIR", str(backup_path))
    monkeypatch.setattr(app_module, "DB_PATH", db_path)
    init_db()
    yield


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def login(client, username=None, password=None):
    return client.post(
        "/login",
        data={
            "username": username or os.environ["AGROQ_ADMIN_USERNAME"],
            "password": password or os.environ["AGROQ_ADMIN_PASSWORD"],
        },
        follow_redirects=False,
    )


def test_quantum_sources_and_health_are_persistent(client):
    login(client)
    health = client.get("/api/quantum/health")
    assert health.status_code == 200
    payload = health.get_json()
    assert payload["ok"] is True
    assert payload["counts"]["sources"] == 22
    assert payload["supported_sequences"] == [
        "Q10",
        "Q2",
        "Q3",
        "Q4",
        "Q5",
        "Q6",
        "Q7",
        "Q8",
        "Q9",
    ]

    sources = client.get("/api/quantum/sources")
    assert sources.status_code == 200
    assert len(sources.get_json()["sources"]) == 22


def test_freeze_dataset_register_run_review_and_artifacts(client):
    login(client)

    frozen = client.post(
        "/api/quantum/datasets/freeze",
        json={
            "name": "Quantum test snapshot",
            "source_tables": ["plots", "observations"],
            "permitted_families": ["Q2", "Q3", "Q4", "Q5", "Q6"],
        },
    )
    assert frozen.status_code == 201
    dataset = frozen.get_json()["dataset"]
    assert dataset["record_count"] >= 6
    assert dataset["sha256"].startswith("sha256:")
    assert dataset["lineage"]

    registered = client.post(
        "/api/quantum/experiments",
        json={
            "experimentId": "AGQ-Q2-PERSISTENT-TEST",
            "sequence": "Q2",
            "title": "Persistent soil sampling test",
            "problemFamily": "Constrained sample selection",
            "sourceIds": ["QRS-001", "QRS-002", "QRS-003"],
            "status": "Registered",
            "runType": "quantum-simulator",
            "algorithm": "Exact + annealing + QAOA",
            "dataset_id": dataset["dataset_id"],
            "formulation": {
                "type": "QUBO",
                "variables": 6,
                "constraints": 1,
            },
            "codeCommit": "pytest",
            "claimControls": {
                "advantageClaim": False,
                "operationalDependency": False,
            },
        },
    )
    assert registered.status_code == 201
    experiment = registered.get_json()["experiment"]
    assert experiment["dataset_id"] == dataset["dataset_id"]

    executed = client.post(
        "/api/quantum/experiments/AGQ-Q2-PERSISTENT-TEST/runs",
        json={
            "configuration": {
                "seed": 301,
                "run_budget": 256,
                "grid_size": 5,
                "sample_budget": 4,
            }
        },
    )
    assert executed.status_code == 201
    run = executed.get_json()["run"]
    assert run["status"] == "completed"
    assert run["result_sha256"].startswith("sha256:")
    assert len(run["solver_results"]) == 3
    assert len(run["artifacts"]) == 2
    assert run["claim_controls"]["advantage_claim"] == 0
    assert run["claim_controls"]["operational_dependency"] == 0

    review = client.post(
        f"/api/quantum/runs/{run['run_id']}/review",
        json={
            "decision": "approved_for_research",
            "notes": "Reviewed frozen lineage, baseline, simulator boundary, and artifacts.",
        },
    )
    assert review.status_code == 201
    assert review.get_json()["review"]["decision"] == "approved_for_research"

    artifacts = client.get(f"/api/quantum/runs/{run['run_id']}/artifacts")
    assert artifacts.status_code == 200
    artifact_id = artifacts.get_json()["artifacts"][0]["artifact_id"]
    download = client.get(f"/api/quantum/artifacts/{artifact_id}")
    assert download.status_code == 200
    assert download.headers["X-AgroQ-SHA256"].startswith("sha256:")


def test_synthetic_browser_record_can_persist_without_backend_dataset(client):
    login(client)
    response = client.post(
        "/api/quantum/experiments",
        json={
            "experimentId": "AGQ-Q5-SYNTHETIC-TEST",
            "sequence": "Q5",
            "title": "Synthetic kernel record",
            "problemFamily": "Supervised classification",
            "sourceIds": ["QRS-005", "QRS-014"],
            "status": "Simulation complete",
            "runType": "quantum-simulator",
            "algorithm": "Classical and quantum kernels",
            "dataset": {
                "id": "BROWSER-SYNTHETIC-DATASET",
                "frozen": True,
                "records": 48,
            },
            "formulation": {"type": "Kernel classification"},
            "codeCommit": "browser-test",
            "claimControls": {
                "advantageClaim": False,
                "operationalDependency": False,
            },
        },
    )
    assert response.status_code == 201
    assert response.get_json()["experiment"]["dataset_id"] is None


def test_viewer_cannot_freeze_or_register_quantum_records(client):
    from werkzeug.security import generate_password_hash

    with get_db() as conn:
        conn.execute(
            """INSERT INTO users(
                user_id, username, display_name, password_hash, role,
                site_id, active, created_at
            ) VALUES(?,?,?,?,?,?,?,?)""",
            (
                "AGQ-USER-QVIEWER",
                "qviewer",
                "Quantum Viewer",
                generate_password_hash("viewer-password"),
                "viewer",
                "AGQ-SITE-001",
                1,
                "2026-01-01T00:00:00+00:00",
            ),
        )

    login(client, username="qviewer", password="viewer-password")
    assert client.get("/api/quantum/health").status_code == 200

    freeze = client.post(
        "/api/quantum/datasets/freeze",
        json={
            "name": "Blocked snapshot",
            "source_tables": ["plots"],
            "permitted_families": ["Q2"],
        },
    )
    assert freeze.status_code == 403

    register = client.post(
        "/api/quantum/experiments",
        json={
            "sequence": "Q2",
            "title": "Blocked experiment",
            "sourceIds": ["QRS-001"],
        },
    )
    assert register.status_code == 403


def test_advantage_and_operational_dependency_claims_are_rejected(client):
    login(client)
    response = client.post(
        "/api/quantum/experiments",
        json={
            "sequence": "Q2",
            "title": "Unsafe claim test",
            "problemFamily": "Test",
            "sourceIds": ["QRS-001"],
            "status": "Registered",
            "runType": "quantum-simulator",
            "claimControls": {
                "advantageClaim": True,
                "operationalDependency": True,
            },
        },
    )
    assert response.status_code == 400
    assert "Advantage claims" in response.get_json()["error"]
