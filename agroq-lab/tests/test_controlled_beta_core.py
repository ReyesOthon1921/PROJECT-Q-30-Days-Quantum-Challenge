import io
import sqlite3
import zipfile
from pathlib import Path

import pytest

from controlled_beta import (
    build_controlled_beta_export,
    create_claim,
    create_interview,
    create_manual_contact,
    create_pilot_record,
    create_persistence_sentinel,
    create_staging_candidate,
    decide_staging_candidate,
    ensure_controlled_beta_schema,
    observe_persistence_sentinel,
    record_acceptance_check,
    review_access_request,
    sync_contact_ledger,
    update_candidate_deployment,
    update_demo_evidence,
)


def utc_now():
    return "2026-07-26T12:00:00+00:00"


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
    schema = (
        Path(__file__).resolve().parents[1]
        / "controlled_beta_schema.sql"
    )
    conn.executescript(schema.read_text(encoding="utf-8"))
    conn.executemany(
        "INSERT INTO users VALUES(?,?,?,?,?,?,?,?)",
        [
            ("U-ADMIN", "admin", "Administrator", "x", "administrator", "S", 1, "now"),
            ("U-ADMIN2", "admin2", "Reviewer", "x", "administrator", "S", 1, "now"),
            ("U-RESEARCH", "research", "Researcher", "x", "researcher", "S", 1, "now"),
            ("U-VIEW", "view", "Viewer", "x", "viewer", "S", 1, "now"),
        ],
    )
    conn.execute(
        """INSERT INTO backup_runs VALUES(
            'B-1','backup.sqlite3','manual','verified',100,'ok',
            'U-ADMIN','now','now'
        )"""
    )
    return conn


def create_candidate(conn):
    return create_staging_candidate(
        conn,
        {
            "commit_sha": "f34aba057daaa103f7a3a8fcc37956bed1e253fd",
            "release_tag": "agroq-q16-rc-f34aba0",
            "backend_url": "https://staging.example",
            "frontend_url": "https://staging.example/app/",
            "service_id": "srv-staging",
        },
        actor_id="U-ADMIN",
        utc_now=utc_now,
    )


def pass_all_checks_and_evidence(conn, candidate_id):
    for row in conn.execute(
        """SELECT check_code FROM staging_acceptance_checks
           WHERE candidate_id=?""",
        (candidate_id,),
    ).fetchall():
        record_acceptance_check(
            conn,
            candidate_id,
            {
                "check_code": row["check_code"],
                "status": "passed",
                "evidence_reference": f"evidence/{row['check_code']}.json",
                "evidence_sha256": "a" * 64,
                "notes": "Verified.",
            },
            actor_id="U-ADMIN",
            utc_now=utc_now,
        )
    for row in conn.execute(
        """SELECT evidence_code FROM demo_evidence_items
           WHERE candidate_id=?""",
        (candidate_id,),
    ).fetchall():
        update_demo_evidence(
            conn,
            candidate_id,
            {
                "evidence_code": row["evidence_code"],
                "status": "verified",
                "file_reference": f"evidence/{row['evidence_code']}.png",
                "sha256": "b" * 64,
                "notes": "Verified.",
            },
            actor_id="U-ADMIN",
            actor_role="administrator",
            utc_now=utc_now,
        )


def test_candidate_is_seeded_with_required_checks_and_evidence():
    conn = make_connection()
    candidate = create_candidate(conn)
    assert len(candidate["checks"]) == 14
    assert len(candidate["demo_evidence"]) == 7
    assert {item["status"] for item in candidate["checks"]} == {"pending"}


def test_acceptance_is_blocked_until_all_gates_pass():
    conn = make_connection()
    candidate = create_candidate(conn)
    with pytest.raises(ValueError):
        decide_staging_candidate(
            conn,
            candidate["candidate_id"],
            {"decision": "accepted", "reason": "Too early."},
            actor_id="U-ADMIN2",
            utc_now=utc_now,
        )

    update_candidate_deployment(
        conn,
        candidate["candidate_id"],
        {"status": "verifying"},
        utc_now=utc_now,
    )
    pass_all_checks_and_evidence(conn, candidate["candidate_id"])
    accepted = decide_staging_candidate(
        conn,
        candidate["candidate_id"],
        {
            "decision": "accepted",
            "reason": "All staging, persistence, evidence, and release gates passed.",
        },
        actor_id="U-ADMIN2",
        utc_now=utc_now,
    )
    assert accepted["status"] == "accepted"
    assert accepted["accepted_by"] == "U-ADMIN2"


def test_persistence_sentinel_updates_restart_and_redeploy_checks():
    conn = make_connection()
    candidate = create_candidate(conn)
    sentinel = create_persistence_sentinel(
        conn,
        candidate["candidate_id"],
        {
            "sentinel_key": "controlled-beta-record",
            "sentinel_value": "persist-me",
        },
        actor_id="U-ADMIN",
        utc_now=utc_now,
    )
    before = observe_persistence_sentinel(
        conn,
        candidate["candidate_id"],
        sentinel["sentinel_id"],
        {
            "phase": "before_restart",
            "observed_value": "persist-me",
        },
        actor_id="U-ADMIN",
        utc_now=utc_now,
    )
    after_restart = observe_persistence_sentinel(
        conn,
        candidate["candidate_id"],
        sentinel["sentinel_id"],
        {
            "phase": "after_restart",
            "observed_value": "persist-me",
        },
        actor_id="U-ADMIN",
        utc_now=utc_now,
    )
    after_redeploy = observe_persistence_sentinel(
        conn,
        candidate["candidate_id"],
        sentinel["sentinel_id"],
        {
            "phase": "after_redeploy",
            "observed_value": "wrong-value",
        },
        actor_id="U-ADMIN",
        utc_now=utc_now,
    )
    assert before["observed"] == 1
    assert after_restart["observed"] == 1
    assert after_redeploy["observed"] == 0
    statuses = {
        row["check_code"]: row["status"]
        for row in conn.execute(
            """SELECT check_code, status
               FROM staging_acceptance_checks
               WHERE candidate_id=? AND check_code IN (
                   'restart_persistence','redeploy_persistence'
               )""",
            (candidate["candidate_id"],),
        ).fetchall()
    }
    assert statuses == {
        "restart_persistence": "passed",
        "redeploy_persistence": "failed",
    }


def test_access_requests_sync_to_contact_ledger_and_review():
    conn = make_connection()
    conn.execute(
        """INSERT INTO access_requests VALUES(
            'AR-1','beta_tester','Taylor Example','taylor@example.com',
            'Farm Lab','Manager','Interested in manual-first beta',
            1,1,'new','now',NULL,NULL
        )"""
    )
    synced = sync_contact_ledger(
        conn,
        actor_id="U-RESEARCH",
        utc_now=utc_now,
    )
    assert synced["inserted"] == 1
    contact = conn.execute(
        "SELECT * FROM beta_contacts WHERE source_id='AR-1'"
    ).fetchone()
    assert contact["status"] == "new"

    reviewed = review_access_request(
        conn,
        "AR-1",
        "approved",
        actor_id="U-ADMIN",
        utc_now=utc_now,
    )
    assert reviewed["status"] == "approved"
    contact = conn.execute(
        "SELECT * FROM beta_contacts WHERE source_id='AR-1'"
    ).fetchone()
    assert contact["status"] == "pilot_candidate"


def test_interview_and_pilot_require_manual_workflow_and_exclusion_scope():
    conn = make_connection()
    contact = create_manual_contact(
        conn,
        {
            "full_name": "Jordan Pilot",
            "email": "jordan@example.com",
            "relationship_type": "customer",
        },
        actor_id="U-RESEARCH",
        utc_now=utc_now,
    )
    interview = create_interview(
        conn,
        {
            "contact_id": contact["contact_id"],
            "interview_type": "discovery",
            "goals": "Reduce manual reporting delay.",
            "pains": "Disconnected spreadsheets.",
            "current_workflow": "Paper log then spreadsheet entry.",
            "success_criteria": "Same-day auditable records.",
            "risk_notes": "No automatic field actions.",
            "decision": "pilot_candidate",
            "completed_at": "2026-07-26T13:00:00+00:00",
        },
        actor_id="U-RESEARCH",
        utc_now=utc_now,
    )
    assert interview["decision"] == "pilot_candidate"

    with pytest.raises(ValueError):
        create_pilot_record(
            conn,
            {
                "contact_id": contact["contact_id"],
                "site_type": "research plot",
                "manual_workflow": "",
                "proposed_scope": "Observation logging.",
                "exclusion_scope": "No equipment control.",
            },
            actor_id="U-RESEARCH",
            utc_now=utc_now,
        )

    pilot = create_pilot_record(
        conn,
        {
            "contact_id": contact["contact_id"],
            "site_type": "research plot",
            "manual_workflow": "Paper observations and manual approval.",
            "available_infrastructure": "Wi-Fi and one laptop.",
            "data_sources": "Manual observations only.",
            "constraints": "No automated equipment control.",
            "proposed_scope": "Observation and task logging.",
            "exclusion_scope": "No sensors, actuation, chemicals, or production claims.",
        },
        actor_id="U-RESEARCH",
        utc_now=utc_now,
    )
    assert pilot["status"] == "draft"


def test_early_quantum_claim_cannot_be_approved():
    conn = make_connection()
    with pytest.raises(ValueError):
        create_claim(
            conn,
            {
                "claim_text": "AgroQ provides quantum advantage.",
                "claim_type": "quantum",
                "evidence_level": "simulation",
                "status": "approved",
                "limitations": "No hardware evidence.",
            },
            actor_id="U-ADMIN",
            actor_role="administrator",
            utc_now=utc_now,
        )

    draft = create_claim(
        conn,
        {
            "claim_text": "AgroQ contains a reproducible quantum-simulation research layer.",
            "claim_type": "quantum",
            "evidence_level": "simulation",
            "status": "draft",
            "limitations": "Simulator evidence only; no advantage or operational dependency claim.",
        },
        actor_id="U-RESEARCH",
        actor_role="researcher",
        utc_now=utc_now,
    )
    assert draft["status"] == "draft"


def test_controlled_beta_export_is_deterministic_and_complete():
    conn = make_connection()
    candidate = create_candidate(conn)
    first, manifest1 = build_controlled_beta_export(
        conn,
        candidate["candidate_id"],
    )
    second, manifest2 = build_controlled_beta_export(
        conn,
        candidate["candidate_id"],
    )
    assert first == second
    assert manifest1["bundle_sha256"] == manifest2["bundle_sha256"]
    with zipfile.ZipFile(io.BytesIO(first)) as archive:
        names = set(archive.namelist())
        assert {
            "staging_candidate.json",
            "acceptance_blockers.json",
            "contact_ledger.json",
            "user_interviews.json",
            "pilot_discovery.json",
            "claims_register.json",
            "invitation_policies.json",
            "access_requests.json",
            "beta_reservations.json",
            "SHA256SUMS.txt",
            "README.md",
        } <= names
