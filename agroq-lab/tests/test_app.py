import os
from pathlib import Path

import pytest
from werkzeug.security import check_password_hash

os.environ["AGROQ_DB_PATH"] = str(Path(__file__).parent / "test_agroq.db")
os.environ["AGROQ_SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["AGROQ_ADMIN_USERNAME"] = "testadmin"
os.environ["AGROQ_ADMIN_PASSWORD"] = "test-password-123"

from app import app, get_db, init_db  # noqa: E402


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


def login(client, username=None, password=None):
    return client.post(
        "/login",
        data={
            "username": username or os.environ["AGROQ_ADMIN_USERNAME"],
            "password": password or os.environ["AGROQ_ADMIN_PASSWORD"],
        },
        follow_redirects=False,
    )


def create_user(username, password, role, user_id=None, display_name=None):
    from werkzeug.security import generate_password_hash

    user_id = user_id or f"AGQ-USER-{username.upper()}"
    display_name = display_name or username.replace("_", " ").title()
    with get_db() as conn:
        conn.execute(
            """INSERT INTO users(
                user_id, username, display_name, password_hash, role, site_id, active, created_at
            ) VALUES(?,?,?,?,?,?,?,?)""",
            (
                user_id,
                username,
                display_name,
                generate_password_hash(password),
                role,
                "AGQ-SITE-001",
                1,
                "2026-01-01T00:00:00+00:00",
            ),
        )


def test_dashboard_loads(client):
    login(client)
    response = client.get("/")
    assert response.status_code == 200
    assert b"Field evidence before automation" in response.data


def test_manual_observation_api(client):
    login(client)
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
    login(client)
    response = client.post(
        "/recommendations/AGQ-REC-001/decision",
        data={"decision": "auto-execute"},
    )
    assert response.status_code == 400


def test_export_json(client):
    login(client)
    response = client.get("/api/export/all.json")
    assert response.status_code == 200
    payload = response.get_json()
    assert "observations" in payload["data"]


def test_login_page_loads(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Sign in to AgroQ" in response.data
    assert b"No external identity provider" in response.data


def test_valid_administrator_login_succeeds(client):
    response = login(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_invalid_password_is_rejected(client):
    response = login(client, password="wrong-password")
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_unauthenticated_browser_access_redirects_to_login(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_unauthenticated_api_access_returns_json_401(client):
    response = client.post(
        "/api/observations",
        json={
            "plot_id": "AGQ-PLOT-001",
            "observed_property": "plant_height",
            "value": 12.5,
            "unit": "cm",
            "source_type": "manual",
        },
    )
    assert response.status_code == 401
    payload = response.get_json()
    assert payload["ok"] is False
    assert "Authentication required" in payload["error"]


def test_viewer_cannot_create_observation(client):
    create_user("viewer_user", "viewer-pass-123", "viewer")
    login(client, username="viewer_user", password="viewer-pass-123")
    response = client.post(
        "/api/observations",
        json={
            "plot_id": "AGQ-PLOT-001",
            "observed_property": "plant_height",
            "value": 12.5,
            "unit": "cm",
            "source_type": "manual",
        },
    )
    assert response.status_code == 403
    assert response.get_json()["error"] == "Insufficient permissions"


def test_field_operator_can_create_observation(client):
    create_user("field_op", "field-pass-123", "field_operator")
    login(client, username="field_op", password="field-pass-123")
    response = client.post(
        "/api/observations",
        json={
            "plot_id": "AGQ-PLOT-001",
            "observed_property": "plant_height",
            "value": 12.5,
            "unit": "cm",
            "source_type": "manual",
        },
    )
    assert response.status_code == 201
    assert response.get_json()["ok"] is True


def test_viewer_cannot_make_recommendation_decision(client):
    create_user("viewer_user", "viewer-pass-123", "viewer")
    login(client, username="viewer_user", password="viewer-pass-123")
    response = client.post(
        "/recommendations/AGQ-REC-001/decision",
        data={"decision": "approved"},
    )
    assert response.status_code == 403


def test_logout_clears_session(client):
    login(client)
    dashboard = client.get("/")
    assert dashboard.status_code == 200

    logout = client.post("/logout", follow_redirects=False)
    assert logout.status_code == 302
    assert "/login" in logout.headers["Location"]

    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_default_site_and_administrator_seeded_once_without_duplication():
    init_db()
    init_db()
    with get_db() as conn:
        site_count = conn.execute("SELECT COUNT(*) AS n FROM sites").fetchone()["n"]
        user_count = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
        site = conn.execute("SELECT * FROM sites WHERE site_id = ?", ("AGQ-SITE-001",)).fetchone()
        admin = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (os.environ["AGROQ_ADMIN_USERNAME"],),
        ).fetchone()
    assert site_count == 1
    assert user_count == 1
    assert site["name"] == "AgroQ One-Acre Living Laboratory"
    assert admin["role"] == "administrator"


def test_password_is_stored_as_hash_and_never_plaintext():
    plaintext = os.environ["AGROQ_ADMIN_PASSWORD"]
    with get_db() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE username = ?",
            (os.environ["AGROQ_ADMIN_USERNAME"],),
        ).fetchone()
    assert row["password_hash"] != plaintext
    assert check_password_hash(row["password_hash"], plaintext)


def test_login_creates_audit_event(client):
    login(client)
    with get_db() as conn:
        event = conn.execute(
            """SELECT * FROM audit_events
               WHERE action = 'login' AND entity_type = 'user'
               ORDER BY created_at DESC LIMIT 1"""
        ).fetchone()
    assert event is not None
    assert event["user_id"] == "AGQ-USER-001"
