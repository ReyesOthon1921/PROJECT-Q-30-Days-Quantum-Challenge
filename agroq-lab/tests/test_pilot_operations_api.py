import io
import zipfile

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


def seed_pilot_prerequisites():
    create_user("pilotparticipant", "viewer")
    with get_db() as conn:
        conn.execute(
            """INSERT INTO beta_contacts(
                contact_id,source_type,source_id,full_name,email,organization,
                relationship_type,status,owner_id,next_action_at,
                consent_contact,consent_updates,notes,created_at,updated_at
            ) VALUES(
                'Q20-CONTACT','manual',NULL,'Pilot Participant',
                'pilot@example.com','Research Plot','beta_tester',
                'pilot_candidate','AGQ-USER-001',NULL,1,1,'',
                '2026-07-26T18:00:00+00:00',
                '2026-07-26T18:00:00+00:00'
            )"""
        )
        conn.execute(
            """INSERT INTO pilot_discovery_records(
                pilot_id,contact_id,site_type,location_region,manual_workflow,
                available_infrastructure,data_sources,constraints,
                proposed_scope,exclusion_scope,status,approved_by,approved_at,
                created_by,created_at,updated_at
            ) VALUES(
                'Q20-PILOT','Q20-CONTACT','research plot','California',
                'Manual observations with supervisor approval.','Laptop',
                'Manual observations','Offline first',
                'Observation and manual task logging.',
                'No sensors, actuation, chemicals, or performance claims.',
                'approved','AGQ-USER-001','2026-07-26T18:00:00+00:00',
                'AGQ-USER-001','2026-07-26T18:00:00+00:00',
                '2026-07-26T18:00:00+00:00'
            )"""
        )
        conn.execute(
            """INSERT INTO staging_candidates(
                candidate_id,commit_sha,release_tag,backend_url,frontend_url,
                service_id,status,notes,created_by,accepted_by,
                created_at,updated_at,accepted_at
            ) VALUES(
                'Q20-STAGE','0a917f9',
                'agroq-controlled-beta-rc-0a917f9',
                'https://staging.example','https://staging.example/app/',
                'srv-staging','accepted','','AGQ-USER-001','AGQ-USER-001',
                '2026-07-26T18:00:00+00:00',
                '2026-07-26T18:00:00+00:00',
                '2026-07-26T18:00:00+00:00'
            )"""
        )


def create_enrollment(client):
    response = client.post(
        "/api/pilots/enrollments",
        json={
            "pilot_id": "Q20-PILOT",
            "candidate_id": "Q20-STAGE",
            "participant_user_id": "AGQ-USER-PILOTPARTICIPANT",
            "support_owner_id": "AGQ-USER-001",
            "cohort_name": "Q20 controlled cohort",
        },
    )
    assert response.status_code == 201
    return response.get_json()["enrollment"]


def complete_activation(client, enrollment):
    enrollment_id = enrollment["enrollment_id"]
    for check in enrollment["onboarding_checks"]:
        response = client.post(
            f"/api/pilots/enrollments/{enrollment_id}/onboarding",
            json={
                "check_code": check["check_code"],
                "status": "completed",
                "evidence_reference": f"evidence/{check['check_code']}.md",
                "notes": "Human verified.",
            },
        )
        assert response.status_code == 200
    for acknowledgment_type in (
        "data_handling",
        "human_control",
        "research_limitations",
    ):
        response = client.post(
            f"/api/pilots/enrollments/{enrollment_id}/acknowledgments",
            json={
                "acknowledgment_type": acknowledgment_type,
                "version": "pilot-v1",
                "accepted": True,
                "evidence_reference": f"ack/{acknowledgment_type}.json",
            },
        )
        assert response.status_code == 201, response.get_json()
    response = client.post(
        f"/api/pilots/enrollments/{enrollment_id}/activate",
        json={"reason": "All Q20 human activation gates passed."},
    )
    assert response.status_code == 200
    return response.get_json()["enrollment"]


def record_metrics_and_interview(client, enrollment_id):
    for index, code in enumerate(("task_time", "record_quality", "offline_success")):
        response = client.post(
            f"/api/pilots/enrollments/{enrollment_id}/metrics",
            json={
                "metric_code": code,
                "metric_name": code.replace("_", " ").title(),
                "baseline_value": 10,
                "target_value": 8,
                "observed_value": 7 + index,
                "unit": "score",
                "direction": "lower" if code == "task_time" else "higher",
                "evidence_reference": f"metrics/{code}.json",
                "evidence_sha256": str(index + 1) * 64,
                "limitations": "Controlled beta with a small sample.",
            },
        )
        assert response.status_code == 201
    with get_db() as conn:
        conn.execute(
            """INSERT INTO beta_interviews(
                interview_id,contact_id,interview_type,scheduled_at,
                completed_at,interviewer_id,goals,pains,current_workflow,
                success_criteria,risk_notes,decision,created_at,updated_at
            ) VALUES(
                'Q22-POST','Q20-CONTACT','post_pilot',
                '2026-07-26T19:00:00+00:00',
                '2026-07-26T20:00:00+00:00','AGQ-USER-001',
                'Review pilot','None','Manual-first workflow',
                'Traceable records','No actuation','continue',
                '2026-07-26T20:00:00+00:00',
                '2026-07-26T20:00:00+00:00'
            )"""
        )


def test_q20_q22_complete_api_flow(client, monkeypatch):
    disable_notification_dispatch(monkeypatch)
    login(client)
    summary = client.get("/api/pilots/operations/summary")
    assert summary.status_code == 200
    assert summary.get_json()["schema_version"] == "AGROQ-PILOT-OPERATIONS-1.0"
    seed_pilot_prerequisites()
    enrollment = create_enrollment(client)
    enrollment_id = enrollment["enrollment_id"]

    blocked = client.post(
        f"/api/pilots/enrollments/{enrollment_id}/activate",
        json={"reason": "Too early."},
    )
    assert blocked.status_code == 409

    active = complete_activation(client, enrollment)
    assert active["status"] == "active"

    feedback = client.post(
        f"/api/pilots/enrollments/{enrollment_id}/feedback",
        json={
            "category": "workflow",
            "rating": 4,
            "description": "Manual records remained available during the test.",
            "context": "Supervised staging trial.",
        },
    )
    assert feedback.status_code == 201

    incident = client.post(
        f"/api/pilots/enrollments/{enrollment_id}/incidents",
        json={
            "severity": "high",
            "category": "data_integrity",
            "title": "Displayed value mismatch",
            "description": "One value did not match its source record.",
            "impact": "The affected evidence cannot be accepted yet.",
            "immediate_manual_action": "Paused entry and preserved the source.",
        },
    )
    assert incident.status_code == 201
    incident_payload = incident.get_json()["incident"]
    assert incident_payload["pilot_status"] == "paused"

    blocked_decision = client.post(
        f"/api/pilots/enrollments/{enrollment_id}/decision",
        json={
            "decision": "recommend_release_review",
            "reason": "This must remain blocked.",
        },
    )
    assert blocked_decision.status_code == 409

    resolved = client.post(
        f"/api/pilots/incidents/{incident_payload['incident_id']}/events",
        json={
            "status": "resolved",
            "notes": "Source and display were reconciled and independently reviewed.",
            "evidence_reference": "incidents/resolution.json",
        },
    )
    assert resolved.status_code == 201
    reactivated = client.post(
        f"/api/pilots/enrollments/{enrollment_id}/activate",
        json={"reason": "Incident evidence was reviewed by the administrator."},
    )
    assert reactivated.status_code == 200

    record_metrics_and_interview(client, enrollment_id)
    decision = client.post(
        f"/api/pilots/enrollments/{enrollment_id}/decision",
        json={
            "decision": "recommend_release_review",
            "reason": "All controlled-pilot evidence gates were human reviewed.",
        },
    )
    assert decision.status_code == 201
    assert decision.get_json()["pilot_decision"]["production_promoted"] is False

    exported = client.get(
        f"/api/pilots/enrollments/{enrollment_id}/evidence.zip"
    )
    assert exported.status_code == 200
    assert len(exported.headers["X-AgroQ-SHA256"]) == 64
    with zipfile.ZipFile(io.BytesIO(exported.data)) as archive:
        assert "SHA256SUMS.txt" in archive.namelist()
        assert "pilot_enrollment.json" in archive.namelist()


def test_pilot_participant_permissions(client, monkeypatch):
    disable_notification_dispatch(monkeypatch)
    login(client)
    assert client.get("/api/pilots/operations/summary").status_code == 200
    seed_pilot_prerequisites()
    enrollment = complete_activation(client, create_enrollment(client))
    enrollment_id = enrollment["enrollment_id"]
    create_user("otherpilotviewer", "viewer")

    clear_session(client)
    login(client, username="pilotparticipant", password="q14-password")
    assert client.get("/api/pilots/operations/summary").status_code == 200
    assert client.post(
        f"/api/pilots/enrollments/{enrollment_id}/feedback",
        json={
            "category": "usability",
            "rating": 5,
            "description": "Participant feedback is allowed.",
        },
    ).status_code == 201
    assert client.post(
        f"/api/pilots/enrollments/{enrollment_id}/metrics",
        json={},
    ).status_code == 403

    clear_session(client)
    login(client, username="otherpilotviewer", password="q14-password")
    assert client.post(
        f"/api/pilots/enrollments/{enrollment_id}/feedback",
        json={
            "category": "usability",
            "description": "This viewer is not the assigned participant.",
        },
    ).status_code == 403
