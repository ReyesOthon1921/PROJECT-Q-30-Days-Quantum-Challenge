import os
from pathlib import Path

import pytest

os.environ["AGROQ_DB_PATH"] = str(Path(__file__).parent / "test_agroq.db")

from app import app, init_db  # noqa: E402


@pytest.fixture(autouse=True)
def clean_db():
    db_path = Path(os.environ["AGROQ_DB_PATH"])
    if db_path.exists():
        db_path.unlink()
    init_db()
    yield
    if db_path.exists():
        db_path.unlink()


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def test_dashboard_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Field evidence before automation" in response.data


def test_manual_observation_api(client):
    response = client.post(
        "/api/observations",
        json={
            "plot_id": "AGQ-PLOT-001",
            "observed_property": "plant_height",
            "value": 12.5,
            "unit": "cm",
            "source_type": "manual",
            "quality_flag": "good",
            "notes": "Test entry",
        },
    )
    assert response.status_code == 201
    assert response.get_json()["ok"] is True


def test_recommendation_requires_valid_decision(client):
    response = client.post(
        "/recommendations/AGQ-REC-001/decision",
        data={"decision": "auto-execute"},
    )
    assert response.status_code == 400


def test_export_json(client):
    response = client.get("/api/export/all.json")
    assert response.status_code == 200
    payload = response.get_json()
    assert "observations" in payload["data"]
