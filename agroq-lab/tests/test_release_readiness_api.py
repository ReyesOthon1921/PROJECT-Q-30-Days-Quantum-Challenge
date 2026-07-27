from test_quantum_backend import (  # noqa: F401
    app_module,
    clean_quantum_db,
    client,
    login,
)

from q14_support import clear_session, create_user



def disable_notification_dispatch(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "dispatch_pending_notifications",
        lambda *_args, **_kwargs: {
            "events_processed": 0,
            "deliveries_processed": 0,
        },
    )


def test_q16_readiness_and_verified_backup_api(client, monkeypatch):
    disable_notification_dispatch(monkeypatch)
    monkeypatch.setenv("WEB_CONCURRENCY", "1")
    monkeypatch.setenv("AGROQ_DEPLOYMENT_MODE", "staging")
    monkeypatch.setenv("AGROQ_BIND_HOST", "0.0.0.0")
    monkeypatch.setenv("AGROQ_DEBUG", "false")
    monkeypatch.setenv(
        "AGROQ_SECRET_KEY",
        "q16-api-test-secret-value-long-enough",
    )

    login(client)
    before = client.get("/api/release/readiness")
    assert before.status_code == 200
    payload = before.get_json()
    assert payload["schema_version"] == "AGROQ-Q16-READINESS-1.0"
    assert any(item["code"] == "VERIFIED_BACKUP" for item in payload["checks"])

    backup = client.post("/api/release/readiness/backup", json={})
    assert backup.status_code == 200
    backup_payload = backup.get_json()
    assert backup_payload["backup"]["status"] == "verified"
    assert backup_payload["recovery"]["passed"] is True
    assert backup_payload["readiness"]["latest_backup"]["status"] == "verified"


def test_q16_viewer_can_read_but_cannot_create_backup(client, monkeypatch):
    disable_notification_dispatch(monkeypatch)
    monkeypatch.setenv("WEB_CONCURRENCY", "1")
    monkeypatch.setenv("AGROQ_DEPLOYMENT_MODE", "staging")
    monkeypatch.setenv("AGROQ_BIND_HOST", "0.0.0.0")
    monkeypatch.setenv("AGROQ_DEBUG", "false")
    monkeypatch.setenv(
        "AGROQ_SECRET_KEY",
        "q16-viewer-test-secret-value-long-enough",
    )

    login(client)
    create_user("q16viewer", "viewer")
    clear_session(client)
    login(client, username="q16viewer", password="q14-password")

    assert client.get("/api/release/readiness").status_code == 200
    assert client.post(
        "/api/release/readiness/backup",
        json={},
    ).status_code == 403
