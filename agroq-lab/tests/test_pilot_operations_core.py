import io
import sqlite3
import zipfile
from pathlib import Path

import pytest

from pilot_operations import (
    REQUIRED_ACKNOWLEDGMENTS,
    activate_enrollment,
    build_pilot_evidence_export,
    create_enrollment,
    create_feedback,
    create_incident,
    decide_pilot_exit,
    ensure_pilot_operations_schema,
    record_acknowledgment,
    record_incident_event,
    record_metric,
    release_review_blockers,
    update_onboarding_check,
)


def utc_now():
    return "2026-07-26T18:00:00+00:00"


def make_connection():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE users(
            user_id TEXT PRIMARY KEY,
            username TEXT,
            display_name TEXT,
            password_hash TEXT,
            role TEXT,
            site_id TEXT,
            active INTEGER,
            created_at TEXT
        );
        CREATE TABLE backup_runs(
            backup_id TEXT PRIMARY KEY,
            filename TEXT,
            trigger_type TEXT,
            status TEXT,
            size_bytes INTEGER,
            verification_message TEXT,
            created_by TEXT,
            created_at TEXT,
            verified_at TEXT
        );
        CREATE TABLE quantum_validation_events(
            validation_id TEXT PRIMARY KEY,
            run_id TEXT,
            dataset_id TEXT,
            gate_type TEXT,
            status TEXT,
            message TEXT,
            report_json TEXT,
            evaluated_by TEXT,
            created_at TEXT
        );
        CREATE TABLE access_requests(
            request_id TEXT PRIMARY KEY,
            relationship_type TEXT,
            full_name TEXT,
            email TEXT,
            organization TEXT,
            role_title TEXT,
            message TEXT,
            consent_contact INTEGER,
            consent_updates INTEGER,
            status TEXT,
            created_at TEXT,
            reviewed_by TEXT,
            reviewed_at TEXT
        );
        CREATE TABLE beta_reservations(
            reservation_id TEXT PRIMARY KEY,
            email TEXT,
            full_name TEXT,
            status TEXT,
            notes TEXT,
            created_at TEXT
        );
        """
    )
    conn.executemany(
        "INSERT INTO users VALUES(?,?,?,?,?,?,?,?)",
        [
            ("U-ADMIN", "admin", "Administrator", "x", "administrator", "S", 1, "now"),
            ("U-RESEARCH", "research", "Researcher", "x", "researcher", "S", 1, "now"),
            ("U-PARTICIPANT", "participant", "Participant", "x", "viewer", "S", 1, "now"),
        ],
    )
    ensure_pilot_operations_schema(conn)
    conn.execute(
        """INSERT INTO beta_contacts(
            contact_id,source_type,source_id,full_name,email,organization,
            relationship_type,status,owner_id,next_action_at,
            consent_contact,consent_updates,notes,created_at,updated_at
        ) VALUES(
            'CONTACT-1','manual',NULL,'Pilot Person','pilot@example.com',
            'Pilot Lab','beta_tester','pilot_candidate','U-ADMIN',NULL,
            1,1,'','now','now'
        )"""
    )
    conn.execute(
        """INSERT INTO pilot_discovery_records(
            pilot_id,contact_id,site_type,location_region,manual_workflow,
            available_infrastructure,data_sources,constraints,proposed_scope,
            exclusion_scope,status,approved_by,approved_at,created_by,
            created_at,updated_at
        ) VALUES(
            'PILOT-1','CONTACT-1','research plot','California',
            'Manual observations with supervisor approval.','Laptop',
            'Manual observations','Offline first',
            'Observation and task logging.',
            'No sensors, actuation, chemicals, or performance claims.',
            'approved','U-ADMIN','now','U-ADMIN','now','now'
        )"""
    )
    conn.execute(
        """INSERT INTO staging_candidates(
            candidate_id,commit_sha,release_tag,backend_url,frontend_url,
            service_id,status,notes,created_by,accepted_by,
            created_at,updated_at,accepted_at
        ) VALUES(
            'STAGE-1','0a917f9','agroq-controlled-beta-rc-0a917f9',
            'https://staging.example','https://staging.example/app/',
            'srv','accepted','','U-ADMIN','U-ADMIN','now','now','now'
        )"""
    )
    return conn


def complete_onboarding(conn, enrollment):
    for check in enrollment["onboarding_checks"]:
        update_onboarding_check(
            conn,
            enrollment["enrollment_id"],
            {
                "check_code": check["check_code"],
                "status": "completed",
                "evidence_reference": f"evidence/{check['check_code']}.md",
            },
            actor_id="U-RESEARCH",
            utc_now=utc_now,
        )
    for acknowledgment_type in REQUIRED_ACKNOWLEDGMENTS:
        record_acknowledgment(
            conn,
            enrollment["enrollment_id"],
            {
                "acknowledgment_type": acknowledgment_type,
                "version": "pilot-v1",
                "accepted": True,
                "evidence_reference": f"ack/{acknowledgment_type}.json",
            },
            actor_id="U-PARTICIPANT",
            utc_now=utc_now,
        )


def create_ready_enrollment(conn):
    enrollment = create_enrollment(
        conn,
        {
            "pilot_id": "PILOT-1",
            "candidate_id": "STAGE-1",
            "participant_user_id": "U-PARTICIPANT",
            "cohort_name": "Founder controlled beta 1",
        },
        actor_id="U-ADMIN",
        utc_now=utc_now,
    )
    complete_onboarding(conn, enrollment)
    return activate_enrollment(
        conn,
        enrollment["enrollment_id"],
        "All human onboarding gates were verified.",
        actor_id="U-ADMIN",
        utc_now=utc_now,
    )


def record_three_metrics(conn, enrollment_id):
    for index, code in enumerate(("task_time", "record_quality", "offline_success")):
        record_metric(
            conn,
            enrollment_id,
            {
                "metric_code": code,
                "metric_name": code.replace("_", " ").title(),
                "baseline_value": 10,
                "target_value": 8,
                "observed_value": 7 + index,
                "unit": "score",
                "direction": "lower" if code == "task_time" else "higher",
                "evidence_reference": f"metrics/{code}.json",
                "evidence_sha256": str(index + 1) * 64,
                "limitations": "Controlled-beta observation; small sample.",
            },
            actor_id="U-RESEARCH",
            utc_now=utc_now,
        )


def test_q20_activation_requires_all_human_gates():
    conn = make_connection()
    enrollment = create_enrollment(
        conn,
        {
            "pilot_id": "PILOT-1",
            "candidate_id": "STAGE-1",
            "participant_user_id": "U-PARTICIPANT",
            "cohort_name": "Cohort A",
        },
        actor_id="U-ADMIN",
        utc_now=utc_now,
    )
    with pytest.raises(ValueError, match="activation is blocked"):
        activate_enrollment(
            conn,
            enrollment["enrollment_id"],
            "Too early.",
            actor_id="U-ADMIN",
            utc_now=utc_now,
        )

    complete_onboarding(conn, enrollment)
    active = activate_enrollment(
        conn,
        enrollment["enrollment_id"],
        "All onboarding evidence and acknowledgments were reviewed.",
        actor_id="U-ADMIN",
        utc_now=utc_now,
    )
    assert active["status"] == "active"
    assert active["activation_blockers"] == []


def test_q21_severe_incident_pauses_pilot_and_preserves_raw_records():
    conn = make_connection()
    enrollment = create_ready_enrollment(conn)
    feedback = create_feedback(
        conn,
        enrollment["enrollment_id"],
        {
            "category": "workflow",
            "rating": 4,
            "description": "Manual observation entry worked offline.",
            "context": "One supervised trial.",
        },
        actor_id="U-PARTICIPANT",
        utc_now=utc_now,
    )
    incident = create_incident(
        conn,
        enrollment["enrollment_id"],
        {
            "severity": "high",
            "category": "data_integrity",
            "title": "Imported record mismatch",
            "description": "A displayed value did not match the source record.",
            "impact": "Pilot evidence cannot be accepted until reviewed.",
            "immediate_manual_action": "Paused entry and preserved the source record.",
        },
        actor_id="U-PARTICIPANT",
        utc_now=utc_now,
    )
    assert incident["pilot_status"] == "paused"
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "UPDATE pilot_feedback SET description='changed' WHERE feedback_id=?",
            (feedback["feedback_id"],),
        )


def test_q22_release_review_requires_evidence_and_never_promotes():
    conn = make_connection()
    enrollment = create_ready_enrollment(conn)
    enrollment_id = enrollment["enrollment_id"]
    create_feedback(
        conn,
        enrollment_id,
        {
            "category": "usability",
            "rating": 4,
            "description": "The manual workflow was understandable.",
        },
        actor_id="U-PARTICIPANT",
        utc_now=utc_now,
    )
    assert release_review_blockers(conn, enrollment_id)
    with pytest.raises(ValueError, match="recommendation is blocked"):
        decide_pilot_exit(
            conn,
            enrollment_id,
            {
                "decision": "recommend_release_review",
                "reason": "Missing required evidence.",
            },
            actor_id="U-ADMIN",
            utc_now=utc_now,
        )

    record_three_metrics(conn, enrollment_id)
    conn.execute(
        """INSERT INTO beta_interviews(
            interview_id,contact_id,interview_type,scheduled_at,completed_at,
            interviewer_id,goals,pains,current_workflow,success_criteria,
            risk_notes,decision,created_at,updated_at
        ) VALUES(
            'POST-1','CONTACT-1','post_pilot','now','now','U-RESEARCH',
            'Review','None','Manual','Traceable','No actuation',
            'continue','now','now'
        )"""
    )
    decision = decide_pilot_exit(
        conn,
        enrollment_id,
        {
            "decision": "recommend_release_review",
            "reason": "Human review found all controlled-pilot gates complete.",
        },
        actor_id="U-ADMIN",
        utc_now=utc_now,
    )
    assert decision["production_promoted"] is False
    assert decision["blocker_summary"]["blockers"] == []

    bundle, manifest = build_pilot_evidence_export(conn, enrollment_id)
    assert len(manifest["bundle_sha256"]) == 64
    with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
        assert {
            "BOUNDARIES.md",
            "SHA256SUMS.txt",
            "claims_register.json",
            "manifest.json",
            "pilot_enrollment.json",
        } <= set(archive.namelist())
