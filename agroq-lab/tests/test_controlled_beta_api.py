import io
import json
import zipfile
from datetime import datetime, timezone

from test_quantum_backend import (  # noqa: F401
    app_module,
    clean_quantum_db,
    client,
    login,
)
from app import get_db
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


def create_candidate(client):
    response = client.post(
        "/api/beta/staging-candidates",
        json={
            "commit_sha": "f34aba057daaa103f7a3a8fcc37956bed1e253fd",
            "release_tag": "agroq-q16-rc-f34aba0",
            "backend_url": "https://staging.example",
            "frontend_url": "https://staging.example/app/",
            "service_id": "srv-staging",
        },
    )
    assert response.status_code == 201
    return response.get_json()["candidate"]


def test_q17_q19_complete_api_flow(client, monkeypatch):
    disable_notification_dispatch(monkeypatch)
    login(client)

    summary = client.get("/api/beta/operations/summary")
    assert summary.status_code == 200
    assert summary.get_json()["schema_version"] == "AGROQ-CONTROLLED-BETA-1.0"
    assert summary.get_json()["active_invitation_policy"]["active"] == 1

    with get_db() as conn:
        conn.execute(
            """INSERT INTO access_requests(
                request_id,relationship_type,full_name,email,organization,
                role_title,message,consent_contact,consent_updates,
                status,created_at
            ) VALUES(
                'AR-Q17','beta_tester','Taylor Example','taylor@example.com',
                'Field Lab','Manager','Manual-first controlled beta',
                1,1,'new','2026-07-26T12:00:00+00:00'
            )"""
        )
        conn.execute(
            """INSERT INTO beta_reservations(
                reservation_id,email,full_name,status,notes,created_at
            ) VALUES(
                'BR-Q17','river@example.com','River Example',
                'interest_recorded','Interested in pilot discovery',
                '2026-07-26T12:00:00+00:00'
            )"""
        )

    sync = client.post("/api/beta/contacts/sync", json={})
    assert sync.status_code == 200
    assert sync.get_json()["sync"]["inserted"] == 2

    refreshed = client.get("/api/beta/operations/summary").get_json()
    assert len(refreshed["contacts"]) == 2
    contact_id = refreshed["contacts"][0]["contact_id"]

    interview = client.post(
        "/api/beta/interviews",
        json={
            "contact_id": contact_id,
            "interview_type": "discovery",
            "goals": "Same-day auditable records.",
            "pains": "Disconnected paper and spreadsheet workflow.",
            "current_workflow": "Paper notes followed by spreadsheet entry.",
            "success_criteria": "Human-reviewed records available the same day.",
            "risk_notes": "No automatic equipment control.",
            "decision": "pilot_candidate",
            "completed_at": "2026-07-26T13:00:00+00:00",
        },
    )
    assert interview.status_code == 201

    pilot = client.post(
        "/api/beta/pilots",
        json={
            "contact_id": contact_id,
            "site_type": "research plot",
            "location_region": "California",
            "manual_workflow": "Paper observations and supervisor approval.",
            "available_infrastructure": "One laptop and Wi-Fi.",
            "data_sources": "Manual observations.",
            "constraints": "Offline-first and no actuation.",
            "proposed_scope": "Observation and manual task logging.",
            "exclusion_scope": "No sensors, chemicals, actuation, or performance claims.",
        },
    )
    assert pilot.status_code == 201

    unsafe_claim = client.post(
        "/api/beta/claims",
        json={
            "claim_text": "AgroQ provides quantum advantage.",
            "claim_type": "quantum",
            "evidence_level": "simulation",
            "status": "approved",
            "limitations": "No hardware evidence.",
        },
    )
    assert unsafe_claim.status_code == 400

    safe_claim = client.post(
        "/api/beta/claims",
        json={
            "claim_text": "AgroQ contains a reproducible quantum-simulation research layer.",
            "claim_type": "quantum",
            "evidence_level": "simulation",
            "status": "draft",
            "limitations": "Simulation only; no advantage or operational dependency claim.",
        },
    )
    assert safe_claim.status_code == 201

    candidate = create_candidate(client)
    candidate_id = candidate["candidate_id"]
    deployment = client.post(
        f"/api/beta/staging-candidates/{candidate_id}/deployment",
        json={
            "status": "verifying",
            "backend_url": "https://staging.example",
            "frontend_url": "https://staging.example/app/",
            "service_id": "srv-staging",
        },
    )
    assert deployment.status_code == 200

    backup = client.post("/api/release/readiness/backup", json={})
    assert backup.status_code == 200
    assert backup.get_json()["backup"]["status"] == "verified"

    detail = client.get(
        f"/api/beta/staging-candidates/{candidate_id}"
    ).get_json()
    for check in detail["candidate"]["checks"]:
        response = client.post(
            f"/api/beta/staging-candidates/{candidate_id}/checks",
            json={
                "check_code": check["check_code"],
                "status": "passed",
                "evidence_reference": f"evidence/{check['check_code']}.json",
                "evidence_sha256": "a" * 64,
                "notes": "Verified in controlled staging.",
            },
        )
        assert response.status_code == 200

    for item in detail["candidate"]["demo_evidence"]:
        response = client.post(
            f"/api/beta/staging-candidates/{candidate_id}/evidence",
            json={
                "evidence_code": item["evidence_code"],
                "status": "verified",
                "file_reference": f"evidence/{item['evidence_code']}.png",
                "sha256": "b" * 64,
                "notes": "Human-verified staging evidence.",
            },
        )
        assert response.status_code == 200

    yc = client.post(
        f"/api/beta/staging-candidates/{candidate_id}/yc-update",
        json={
            "headline": "AgroQ completed controlled-beta code readiness.",
            "summary": "Persistent staging, access, research, and evidence controls are implemented.",
            "metrics": {"tests_passed": 1, "staging_checks": 14},
            "limitations": "No production promotion, field integration, or quantum-advantage claim.",
        },
    )
    assert yc.status_code == 201

    decision = client.post(
        f"/api/beta/staging-candidates/{candidate_id}/decision",
        json={
            "decision": "accepted",
            "reason": "All staging checks, evidence, backup, and scientific gates passed.",
        },
    )
    assert decision.status_code == 200
    assert decision.get_json()["candidate"]["status"] == "accepted"

    exported = client.get(
        f"/api/beta/staging-candidates/{candidate_id}/evidence.zip"
    )
    assert exported.status_code == 200
    assert exported.headers["X-AgroQ-SHA256"]
    with zipfile.ZipFile(io.BytesIO(exported.data)) as archive:
        assert "SHA256SUMS.txt" in archive.namelist()
        assert "staging_candidate.json" in archive.namelist()
        assert "claims_register.json" in archive.namelist()


def test_controlled_beta_role_permissions(client, monkeypatch):
    disable_notification_dispatch(monkeypatch)
    login(client)
    create_user("q17researcher", "researcher")
    create_user("q17viewer", "viewer")

    clear_session(client)
    login(client, username="q17researcher", password="q14-password")
    assert client.get("/api/beta/operations/summary").status_code == 200
    assert client.post(
        "/api/beta/staging-candidates",
        json={"commit_sha": "1234567", "release_tag": "blocked"},
    ).status_code == 403
    assert client.post(
        "/api/beta/claims",
        json={
            "claim_text": "Prototype workflow exists.",
            "claim_type": "product",
            "evidence_level": "prototype",
            "status": "draft",
            "limitations": "Controlled-beta evidence is not complete.",
        },
    ).status_code == 201

    clear_session(client)
    login(client, username="q17viewer", password="q14-password")
    assert client.get("/api/beta/operations/summary").status_code == 200
    assert client.post("/api/beta/contacts/sync", json={}).status_code == 403
    assert client.post(
        "/api/beta/claims",
        json={
            "claim_text": "Blocked.",
            "claim_type": "product",
            "evidence_level": "idea",
            "status": "draft",
            "limitations": "Blocked.",
        },
    ).status_code == 403


def test_invitation_policy_caps_admin_invites(client, monkeypatch):
    disable_notification_dispatch(monkeypatch)
    login(client)
    assert client.get("/api/beta/operations/summary").status_code == 200

    with client.session_transaction() as session:
        session["access_csrf"] = "q17-csrf-token"

    response = client.post(
        "/admin/access",
        data={
            "csrf_token": "q17-csrf-token",
            "relationship_type": "beta_tester",
            "role": "viewer",
            "email": "invitee@example.com",
            "expires_days": "90",
            "max_uses": "25",
            "note": "Controlled beta invitation.",
        },
    )
    assert response.status_code == 200

    with get_db() as conn:
        invite = conn.execute(
            "SELECT * FROM invite_codes ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
    assert invite["max_uses"] == 5
    expires = datetime.fromisoformat(invite["expires_at"])
    remaining = expires - datetime.now(timezone.utc)
    assert 13 <= remaining.days <= 14
