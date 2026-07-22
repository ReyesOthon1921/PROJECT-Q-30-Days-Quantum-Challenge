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


def plot_payload(**overrides):
    values = {
        "plot_id": "AGQ-PLOT-TEST",
        "name": "Test Plot",
        "plot_type": "observation",
        "area": "0.05 acre",
        "status": "Active",
    }
    values.update(overrides)
    return values


def asset_payload(**overrides):
    values = {
        "asset_id": "AGQ-ASSET-TEST",
        "name": "Test Asset",
        "asset_type": "manual-tool",
        "plot_id": "AGQ-PLOT-001",
        "status": "available",
    }
    values.update(overrides)
    return values


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


def test_administrator_can_create_edit_and_retire_plot(client):
    login(client)
    created = client.post("/plots/new", data=plot_payload(), follow_redirects=False)
    assert created.status_code == 302
    edited = client.post(
        "/plots/AGQ-PLOT-TEST/edit",
        data=plot_payload(name="Updated Test Plot"),
        follow_redirects=False,
    )
    assert edited.status_code == 302
    retired = client.post("/plots/AGQ-PLOT-TEST/retire", follow_redirects=False)
    assert retired.status_code == 302
    with get_db() as conn:
        plot = conn.execute(
            "SELECT * FROM plots WHERE plot_id = 'AGQ-PLOT-TEST'"
        ).fetchone()
        actions = {
            row["action"] for row in conn.execute(
                "SELECT action FROM audit_events WHERE entity_id = 'AGQ-PLOT-TEST'"
            ).fetchall()
        }
    assert plot["name"] == "Updated Test Plot"
    assert plot["status"] == "Retired"
    assert {"plot_created", "plot_updated", "plot_retired"} <= actions


def test_researcher_can_create_and_edit_but_not_retire_plot(client):
    create_user("researcher", "research-pass", "researcher")
    login(client, "researcher", "research-pass")
    assert client.post("/plots/new", data=plot_payload()).status_code == 302
    assert client.post(
        "/plots/AGQ-PLOT-TEST/edit", data=plot_payload(name="Research Plot")
    ).status_code == 302
    assert client.post("/plots/AGQ-PLOT-TEST/retire").status_code == 403


def test_viewer_can_view_registry_but_cannot_create_or_edit_plot(client):
    create_user("registry_viewer", "viewer-pass", "viewer")
    login(client, "registry_viewer", "viewer-pass")
    assert client.get("/registry").status_code == 200
    assert client.get("/plots/AGQ-PLOT-001").status_code == 200
    assert client.post("/plots/new", data=plot_payload()).status_code == 403
    assert client.post(
        "/plots/AGQ-PLOT-001/edit", data=plot_payload()
    ).status_code == 403


def test_plot_duplicate_id_is_rejected_safely(client):
    login(client)
    response = client.post(
        "/plots/new", data=plot_payload(plot_id="AGQ-PLOT-001"), follow_redirects=True
    )
    assert response.status_code == 200
    assert b"already exists" in response.data


def test_missing_plot_returns_404(client):
    login(client)
    assert client.get("/plots/DOES-NOT-EXIST").status_code == 404


def test_plot_retirement_is_post_only_and_dependencies_block_it(client):
    login(client)
    assert client.get("/plots/AGQ-PLOT-001/retire").status_code == 405
    response = client.post("/plots/AGQ-PLOT-001/retire", follow_redirects=True)
    assert response.status_code == 200
    assert b"cannot be retired" in response.data
    with get_db() as conn:
        status = conn.execute(
            "SELECT status FROM plots WHERE plot_id = 'AGQ-PLOT-001'"
        ).fetchone()["status"]
    assert status == "Active"


def test_administrator_can_create_edit_and_retire_asset_with_revision(client):
    login(client)
    assert client.post("/assets/new", data=asset_payload()).status_code == 302
    assert client.post(
        "/assets/AGQ-ASSET-TEST/edit",
        data=asset_payload(name="Updated Asset", status="testing"),
    ).status_code == 302
    with get_db() as conn:
        updated = conn.execute(
            "SELECT * FROM assets WHERE asset_id = 'AGQ-ASSET-TEST'"
        ).fetchone()
    assert updated["revision"] == "rev-b"
    assert client.post("/assets/AGQ-ASSET-TEST/retire").status_code == 302
    with get_db() as conn:
        asset = conn.execute(
            "SELECT * FROM assets WHERE asset_id = 'AGQ-ASSET-TEST'"
        ).fetchone()
        actions = {
            row["action"] for row in conn.execute(
                "SELECT action FROM audit_events WHERE entity_id = 'AGQ-ASSET-TEST'"
            ).fetchall()
        }
    assert asset["status"] == "retired"
    assert asset["revision"] == "rev-c"
    assert {"asset_created", "asset_updated", "asset_retired"} <= actions


def test_invalid_asset_plot_assignment_is_rejected(client):
    login(client)
    response = client.post(
        "/assets/new", data=asset_payload(plot_id="MISSING-PLOT"), follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Assigned plot does not exist" in response.data


def observation_payload(**overrides):
    values = {
        "observation_id": "AGQ-OBS-TEST",
        "plot_id": "AGQ-PLOT-001",
        "asset_id": "",
        "observed_property": "soil_moisture",
        "value": "31.5",
        "unit": "%",
        "source_type": "manual",
        "quality_flag": "good",
        "notes": "Manual field reading",
        "observed_at": "2026-07-22T10:30",
    }
    values.update(overrides)
    return values


def test_field_operator_can_record_and_retrieve_manual_observation(client):
    create_user("observer", "observer-pass", "field_operator")
    login(client, "observer", "observer-pass")
    created = client.post("/observations/new", data=observation_payload())
    assert created.status_code == 302
    detail = client.get("/observations/AGQ-OBS-TEST")
    assert detail.status_code == 200
    assert b"31.5" in detail.data
    assert b"Manual field reading" in detail.data


def test_observation_validation_rejects_bad_source_and_missing_plot(client):
    login(client)
    bad_source = client.post(
        "/api/observations", json=observation_payload(source_type="unknown")
    )
    assert bad_source.status_code == 400
    missing_plot = client.post(
        "/api/observations", json=observation_payload(plot_id="MISSING")
    )
    assert missing_plot.status_code == 400


def test_correction_preserves_raw_observation_and_creates_audit_record(client):
    login(client)
    with get_db() as conn:
        before = dict(conn.execute(
            "SELECT * FROM observations WHERE observation_id = 'AGQ-OBS-001'"
        ).fetchone())
    response = client.post(
        "/observations/AGQ-OBS-001/corrections/new",
        data={
            "value": "25.0",
            "unit": "%",
            "quality_flag": "corrected",
            "notes": "Transcription corrected from field sheet.",
            "reason": "Original value was entered incorrectly.",
        },
    )
    assert response.status_code == 302
    with get_db() as conn:
        after = dict(conn.execute(
            "SELECT * FROM observations WHERE observation_id = 'AGQ-OBS-001'"
        ).fetchone())
        correction = conn.execute(
            "SELECT * FROM observation_corrections WHERE observation_id = 'AGQ-OBS-001'"
        ).fetchone()
        audit = conn.execute(
            "SELECT * FROM audit_events WHERE action = 'observation_corrected'"
        ).fetchone()
    assert after == before
    assert correction["value"] == 25.0
    assert correction["reason"] == "Original value was entered incorrectly."
    assert audit["entity_id"] == correction["correction_id"]


def test_correction_requires_reason_and_authorized_role(client):
    login(client)
    missing_reason = client.post(
        "/observations/AGQ-OBS-001/corrections/new",
        data={"value": "25", "unit": "%", "quality_flag": "corrected"},
    )
    assert missing_reason.status_code == 400
    create_user("readonly", "readonly-pass", "viewer")
    client.post("/logout")
    login(client, "readonly", "readonly-pass")
    forbidden = client.post(
        "/observations/AGQ-OBS-001/corrections/new",
        data={"value": "25", "unit": "%", "quality_flag": "corrected", "reason": "test"},
    )
    assert forbidden.status_code == 403


def test_observation_routes_do_not_allow_update_or_delete(client):
    login(client)
    assert client.put("/observations/AGQ-OBS-001", data={"value": "0"}).status_code == 405
    assert client.delete("/observations/AGQ-OBS-001").status_code == 405


def test_asset_duplicate_id_is_rejected_safely(client):
    login(client)
    response = client.post(
        "/assets/new", data=asset_payload(asset_id="AGQ-ASSET-001"),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"already exists" in response.data


def test_researcher_cannot_retire_asset(client):
    create_user("asset_researcher", "research-pass", "researcher")
    login(client, "asset_researcher", "research-pass")
    assert client.post("/assets/AGQ-ASSET-001/retire").status_code == 403


def test_field_operator_cannot_create_asset(client):
    create_user("asset_operator", "operator-pass", "field_operator")
    login(client, "asset_operator", "operator-pass")
    assert client.post("/assets/new", data=asset_payload()).status_code == 403


def test_missing_asset_returns_404_and_retirement_is_post_only(client):
    login(client)
    assert client.get("/assets/DOES-NOT-EXIST").status_code == 404
    assert client.get("/assets/AGQ-ASSET-001/retire").status_code == 405


def experiment_payload(**overrides):
    values = {
        "experiment_id": "AGQ-EXP-TEST",
        "title": "Compost comparison",
        "hypothesis": "Compost treatment improves soil moisture retention.",
        "status": "draft",
        "plot_id": "AGQ-PLOT-001",
    }
    values.update(overrides)
    return values


def test_researcher_can_create_experiment_and_treatment(client):
    create_user("exp_researcher", "research-pass", "researcher")
    login(client, "exp_researcher", "research-pass")
    assert client.post("/experiments/new", data=experiment_payload()).status_code == 302
    assert client.post(
        "/experiments/AGQ-EXP-TEST/treatments",
        data={"treatment_id": "AGQ-TRT-TEST", "name": "Compost", "description": "Standard rate"},
    ).status_code == 302
    with get_db() as conn:
        experiment = conn.execute("SELECT * FROM experiments WHERE experiment_id='AGQ-EXP-TEST'").fetchone()
        treatment = conn.execute("SELECT * FROM treatments WHERE treatment_id='AGQ-TRT-TEST'").fetchone()
    assert experiment["owner"] == "AGQ-USER-EXP_RESEARCHER"
    assert treatment["experiment_id"] == experiment["experiment_id"]


def test_assignment_requires_treatment_from_same_experiment(client):
    login(client)
    response = client.post(
        "/experiments/AGQ-EXP-001/assignments",
        data={"treatment_id": "MISSING", "plot_id": "AGQ-PLOT-001", "responsible_user_id": "AGQ-USER-001"},
    )
    assert response.status_code == 400
    assert b"does not belong" in response.data


def test_treatment_assignment_records_plot_and_responsible_user(client):
    login(client)
    client.post("/experiments/AGQ-EXP-001/treatments", data={"treatment_id": "AGQ-TRT-ASSIGN", "name": "Control", "is_control": "1"})
    response = client.post(
        "/experiments/AGQ-EXP-001/assignments",
        data={"assignment_id": "AGQ-ASN-TEST", "treatment_id": "AGQ-TRT-ASSIGN", "plot_id": "AGQ-PLOT-003",
              "responsible_user_id": "AGQ-USER-001", "start_date": "2026-07-23"},
    )
    assert response.status_code == 302
    with get_db() as conn:
        row = conn.execute("SELECT * FROM treatment_assignments WHERE assignment_id='AGQ-ASN-TEST'").fetchone()
    assert row["plot_id"] == "AGQ-PLOT-003"
    assert row["responsible_user_id"] == "AGQ-USER-001"


def test_status_change_preserves_history_and_requires_reason(client):
    login(client)
    assert client.post("/experiments/AGQ-EXP-001/status", data={"status": "paused", "reason": "Awaiting baseline readings"}).status_code == 302
    assert client.post("/experiments/AGQ-EXP-001/status", data={"status": "active", "reason": ""}).status_code == 400
    with get_db() as conn:
        experiment = conn.execute("SELECT * FROM experiments WHERE experiment_id='AGQ-EXP-001'").fetchone()
        history = conn.execute("SELECT * FROM experiment_status_history WHERE experiment_id='AGQ-EXP-001'").fetchone()
    assert experiment["status"] == "paused"
    assert history["previous_status"] == "active"
    assert history["new_status"] == "paused"


def test_outcome_links_immutable_observation_without_copying_value(client):
    login(client)
    with get_db() as conn:
        before = dict(conn.execute("SELECT * FROM observations WHERE observation_id='AGQ-OBS-001'").fetchone())
    response = client.post(
        "/experiments/AGQ-EXP-001/outcomes",
        data={"observation_id": "AGQ-OBS-001", "interpretation": "Baseline outcome"},
    )
    assert response.status_code == 302
    with get_db() as conn:
        after = dict(conn.execute("SELECT * FROM observations WHERE observation_id='AGQ-OBS-001'").fetchone())
        outcome = conn.execute("SELECT * FROM experiment_outcomes WHERE experiment_id='AGQ-EXP-001'").fetchone()
    assert before == after
    assert outcome["observation_id"] == "AGQ-OBS-001"


def test_viewer_can_view_but_cannot_design_experiment(client):
    create_user("exp_viewer", "viewer-pass", "viewer")
    login(client, "exp_viewer", "viewer-pass")
    assert client.get("/experiments").status_code == 200
    assert client.get("/experiments/AGQ-EXP-001").status_code == 200
    assert client.post("/experiments/new", data=experiment_payload()).status_code == 403
    assert client.post("/experiments/AGQ-EXP-001/status", data={"status": "paused", "reason": "test"}).status_code == 403
