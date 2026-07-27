from __future__ import annotations

import hashlib
import io
import json
import sqlite3
import time
import zipfile
from pathlib import Path
from typing import Any, Callable

Q17_Q19_SCHEMA_VERSION = "AGROQ-CONTROLLED-BETA-1.0"
VIEW_ROLES = ("administrator", "researcher", "field_operator", "viewer")
OPERATIONS_ROLES = ("administrator", "researcher")
ADMIN_ROLES = ("administrator",)
BASE_DIR = Path(__file__).resolve().parent

REQUIRED_STAGING_CHECKS: tuple[tuple[str, str, str], ...] = (
    ("backend_health", "backend", "Backend health endpoint returns HTTP 200."),
    ("frontend_overview", "frontend", "Overview page loads in staging."),
    ("frontend_digital_acre", "frontend", "3D Digital Acre page loads in staging."),
    ("access_community", "frontend", "Access & Community page loads in staging."),
    ("quantum_lab", "frontend", "Quantum Lab page loads in staging."),
    ("authenticated_login", "access", "Administrator login succeeds in staging."),
    ("access_request_submission", "access", "Public access request is stored and reviewable."),
    ("beta_reservation_submission", "access", "Beta reservation is stored and reviewable."),
    ("invitation_redemption", "access", "Invitation redemption creates the intended role."),
    ("admin_access_review", "access", "Administrator access-review workflow succeeds."),
    ("restart_persistence", "persistence", "Records survive a service restart."),
    ("redeploy_persistence", "persistence", "Records survive a replacement deployment."),
    ("manual_release_boundary", "release", "Release remains an explicit administrator decision."),
    ("rollback_checkpoint", "rollback", "Previous release and verified backup are documented."),
)

REQUIRED_DEMO_EVIDENCE: tuple[tuple[str, str], ...] = (
    ("overview_screenshot", "Overview screenshot"),
    ("digital_acre_screenshot", "3D Digital Acre screenshot"),
    ("access_community_screenshot", "Access & Community screenshot"),
    ("quantum_lab_screenshot", "Quantum Lab screenshot"),
    ("backup_demo_recording", "Three-minute backup demonstration recording"),
    ("architecture_summary", "Current architecture summary"),
    ("limitations_statement", "Current limitations statement"),
)

DEFAULT_INVITATION_POLICY = {
    "max_expiry_days": 14,
    "default_max_uses": 1,
    "absolute_max_uses": 5,
    "email_binding_required": False,
    "single_use_recommended": True,
    "allowed_roles": ["viewer", "researcher", "field_operator"],
    "public_administrator_invites": False,
    "audit_required": True,
    "revoke_after_final_use": True,
}


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _json_load(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _new_id(prefix: str) -> str:
    return f"AGQ-{prefix}-{time.time_ns()}"


def _row(
    conn: sqlite3.Connection,
    query: str,
    params: tuple[Any, ...],
    error: str,
) -> sqlite3.Row:
    result = conn.execute(query, params).fetchone()
    if result is None:
        raise ValueError(error)
    return result


def _candidate_row(
    conn: sqlite3.Connection,
    candidate_id: str,
) -> sqlite3.Row:
    return _row(
        conn,
        "SELECT * FROM staging_candidates WHERE candidate_id=?",
        (candidate_id,),
        "Staging candidate not found.",
    )


def ensure_controlled_beta_schema(
    conn: sqlite3.Connection,
    *,
    created_by: str | None = None,
    utc_now: Callable[[], str] | None = None,
) -> None:
    access_schema = BASE_DIR / "access_schema.sql"
    if access_schema.is_file():
        conn.executescript(access_schema.read_text(encoding="utf-8"))
    conn.executescript(
        (BASE_DIR / "controlled_beta_schema.sql").read_text(encoding="utf-8")
    )

    existing = conn.execute(
        "SELECT 1 FROM invitation_policies WHERE active=1"
    ).fetchone()
    if existing is None and created_by:
        now = utc_now() if utc_now else ""
        conn.execute(
            """INSERT INTO invitation_policies(
                policy_id, version, active, policy_json,
                approved_by, approved_at, created_by, created_at
            ) VALUES(?,?,1,?,?,?,?,?)""",
            (
                _new_id("INVITEPOL"),
                "controlled-beta-v1",
                canonical_json(DEFAULT_INVITATION_POLICY),
                created_by,
                now,
                created_by,
                now,
            ),
        )


def _serialize_candidate(
    conn: sqlite3.Connection,
    candidate: sqlite3.Row,
    *,
    include_details: bool = True,
) -> dict[str, Any]:
    record = dict(candidate)
    if not include_details:
        return record

    record["checks"] = [
        dict(row)
        for row in conn.execute(
            """SELECT * FROM staging_acceptance_checks
               WHERE candidate_id=?
               ORDER BY category, check_code""",
            (candidate["candidate_id"],),
        ).fetchall()
    ]
    record["persistence_sentinels"] = [
        dict(row)
        for row in conn.execute(
            """SELECT s.*,
                      (SELECT COUNT(*) FROM staging_persistence_observations o
                       WHERE o.sentinel_id=s.sentinel_id) AS observation_count
               FROM staging_persistence_sentinels s
               WHERE s.candidate_id=?
               ORDER BY s.created_at""",
            (candidate["candidate_id"],),
        ).fetchall()
    ]
    record["persistence_observations"] = [
        dict(row)
        for row in conn.execute(
            """SELECT * FROM staging_persistence_observations
               WHERE candidate_id=?
               ORDER BY checked_at, observation_id""",
            (candidate["candidate_id"],),
        ).fetchall()
    ]
    record["decisions"] = []
    for row in conn.execute(
        """SELECT * FROM staging_acceptance_decisions
           WHERE candidate_id=?
           ORDER BY decided_at DESC""",
        (candidate["candidate_id"],),
    ).fetchall():
        item = dict(row)
        item["blocker_summary"] = _json_load(
            item.pop("blocker_summary_json", None),
            {},
        )
        record["decisions"].append(item)

    record["demo_evidence"] = [
        dict(row)
        for row in conn.execute(
            """SELECT * FROM demo_evidence_items
               WHERE candidate_id=?
               ORDER BY evidence_code""",
            (candidate["candidate_id"],),
        ).fetchall()
    ]
    record["yc_updates"] = []
    for row in conn.execute(
        """SELECT * FROM yc_update_snapshots
           WHERE candidate_id=?
           ORDER BY created_at DESC""",
        (candidate["candidate_id"],),
    ).fetchall():
        item = dict(row)
        item["metrics"] = _json_load(item.pop("metrics_json", None), {})
        item["evidence_manifest"] = _json_load(
            item.pop("evidence_manifest_json", None),
            {},
        )
        record["yc_updates"].append(item)
    record["exports"] = []
    for row in conn.execute(
        """SELECT * FROM controlled_beta_exports
           WHERE candidate_id=?
           ORDER BY created_at DESC""",
        (candidate["candidate_id"],),
    ).fetchall():
        item = dict(row)
        item["manifest"] = _json_load(item.pop("manifest_json", None), {})
        record["exports"].append(item)
    return record


def create_staging_candidate(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    commit_sha = str(payload.get("commit_sha", "")).strip()
    release_tag = str(payload.get("release_tag", "")).strip()
    if len(commit_sha) < 7:
        raise ValueError("A release commit SHA is required.")
    if not release_tag:
        raise ValueError("A release-candidate tag is required.")

    candidate_id = str(
        payload.get("candidate_id") or _new_id("STAGE")
    ).strip()
    now = utc_now()
    conn.execute(
        """INSERT INTO staging_candidates(
            candidate_id, commit_sha, release_tag, backend_url,
            frontend_url, service_id, status, notes, created_by,
            accepted_by, created_at, updated_at, accepted_at
        ) VALUES(?,?,?,?,?,?,'draft',?,?,NULL,?,?,NULL)""",
        (
            candidate_id,
            commit_sha,
            release_tag,
            str(payload.get("backend_url", "")).strip() or None,
            str(payload.get("frontend_url", "")).strip() or None,
            str(payload.get("service_id", "")).strip() or None,
            str(payload.get("notes", "")).strip(),
            actor_id,
            now,
            now,
        ),
    )

    for code, category, description in REQUIRED_STAGING_CHECKS:
        conn.execute(
            """INSERT INTO staging_acceptance_checks(
                check_id, candidate_id, check_code, category, status,
                evidence_reference, evidence_sha256, notes,
                checked_by, checked_at, created_at
            ) VALUES(?,?,?,?, 'pending', NULL, NULL, ?, NULL, NULL, ?)""",
            (
                _new_id("STAGECHECK"),
                candidate_id,
                code,
                category,
                description,
                now,
            ),
        )

    for code, title in REQUIRED_DEMO_EVIDENCE:
        conn.execute(
            """INSERT INTO demo_evidence_items(
                item_id, candidate_id, evidence_code, title, status,
                file_reference, sha256, notes, captured_at,
                verified_by, verified_at, created_at
            ) VALUES(?,?,?,?,'missing',NULL,NULL,'',NULL,NULL,NULL,?)""",
            (
                _new_id("DEMO"),
                candidate_id,
                code,
                title,
                now,
            ),
        )

    return _serialize_candidate(
        conn,
        _candidate_row(conn, candidate_id),
    )


def update_candidate_deployment(
    conn: sqlite3.Connection,
    candidate_id: str,
    payload: dict[str, Any],
    *,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    candidate = _candidate_row(conn, candidate_id)
    status = str(payload.get("status", candidate["status"])).strip()
    if status not in {"draft", "deployed", "verifying"}:
        raise ValueError("Deployment status must be draft, deployed, or verifying.")
    conn.execute(
        """UPDATE staging_candidates
           SET backend_url=?, frontend_url=?, service_id=?,
               status=?, notes=?, updated_at=?
           WHERE candidate_id=?""",
        (
            str(payload.get("backend_url", candidate["backend_url"] or "")).strip()
            or None,
            str(payload.get("frontend_url", candidate["frontend_url"] or "")).strip()
            or None,
            str(payload.get("service_id", candidate["service_id"] or "")).strip()
            or None,
            status,
            str(payload.get("notes", candidate["notes"] or "")).strip(),
            utc_now(),
            candidate_id,
        ),
    )
    return _serialize_candidate(
        conn,
        _candidate_row(conn, candidate_id),
    )


def record_acceptance_check(
    conn: sqlite3.Connection,
    candidate_id: str,
    payload: dict[str, Any],
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    _candidate_row(conn, candidate_id)
    check_code = str(payload.get("check_code", "")).strip()
    status = str(payload.get("status", "")).strip()
    if status not in {"pending", "passed", "failed", "blocked", "not_applicable"}:
        raise ValueError("A valid acceptance-check status is required.")
    check = _row(
        conn,
        """SELECT * FROM staging_acceptance_checks
           WHERE candidate_id=? AND check_code=?""",
        (candidate_id, check_code),
        "Acceptance check not found.",
    )
    evidence_reference = str(
        payload.get("evidence_reference", "")
    ).strip() or None
    evidence_sha256 = str(payload.get("evidence_sha256", "")).strip() or None
    if evidence_sha256 and len(evidence_sha256) not in {64, 71}:
        raise ValueError("Evidence SHA-256 must contain a valid digest.")
    conn.execute(
        """UPDATE staging_acceptance_checks
           SET status=?, evidence_reference=?, evidence_sha256=?,
               notes=?, checked_by=?, checked_at=?
           WHERE check_id=?""",
        (
            status,
            evidence_reference,
            evidence_sha256,
            str(payload.get("notes", "")).strip(),
            actor_id,
            utc_now(),
            check["check_id"],
        ),
    )
    return dict(
        _row(
            conn,
            "SELECT * FROM staging_acceptance_checks WHERE check_id=?",
            (check["check_id"],),
            "Acceptance check not found.",
        )
    )


def create_persistence_sentinel(
    conn: sqlite3.Connection,
    candidate_id: str,
    payload: dict[str, Any],
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    _candidate_row(conn, candidate_id)
    sentinel_key = str(payload.get("sentinel_key", "")).strip()
    sentinel_value = str(payload.get("sentinel_value", "")).strip()
    if not sentinel_key:
        raise ValueError("sentinel_key is required.")
    if not sentinel_value:
        raise ValueError("sentinel_value is required.")
    sentinel_id = _new_id("SENTINEL")
    conn.execute(
        """INSERT INTO staging_persistence_sentinels(
            sentinel_id, candidate_id, sentinel_key,
            sentinel_value_sha256, created_by, created_at
        ) VALUES(?,?,?,?,?,?)""",
        (
            sentinel_id,
            candidate_id,
            sentinel_key,
            sha256_text(sentinel_value),
            actor_id,
            utc_now(),
        ),
    )
    return dict(
        _row(
            conn,
            """SELECT * FROM staging_persistence_sentinels
               WHERE sentinel_id=?""",
            (sentinel_id,),
            "Persistence sentinel not found.",
        )
    )


def observe_persistence_sentinel(
    conn: sqlite3.Connection,
    candidate_id: str,
    sentinel_id: str,
    payload: dict[str, Any],
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    sentinel = _row(
        conn,
        """SELECT * FROM staging_persistence_sentinels
           WHERE sentinel_id=? AND candidate_id=?""",
        (sentinel_id, candidate_id),
        "Persistence sentinel not found.",
    )
    phase = str(payload.get("phase", "")).strip()
    if phase not in {"before_restart", "after_restart", "after_redeploy"}:
        raise ValueError("A valid persistence phase is required.")
    observed_value = str(payload.get("observed_value", "")).strip()
    observed_sha256 = sha256_text(observed_value) if observed_value else None
    observed = bool(
        observed_sha256
        and observed_sha256 == sentinel["sentinel_value_sha256"]
    )
    observation_id = _new_id("PERSIST")
    conn.execute(
        """INSERT INTO staging_persistence_observations(
            observation_id, sentinel_id, candidate_id, phase,
            observed, observed_sha256, notes, checked_by, checked_at
        ) VALUES(?,?,?,?,?,?,?,?,?)""",
        (
            observation_id,
            sentinel_id,
            candidate_id,
            phase,
            1 if observed else 0,
            observed_sha256,
            str(payload.get("notes", "")).strip(),
            actor_id,
            utc_now(),
        ),
    )
    check_code = (
        "restart_persistence"
        if phase == "after_restart"
        else "redeploy_persistence"
        if phase == "after_redeploy"
        else None
    )
    if check_code:
        record_acceptance_check(
            conn,
            candidate_id,
            {
                "check_code": check_code,
                "status": "passed" if observed else "failed",
                "evidence_reference": observation_id,
                "evidence_sha256": observed_sha256,
                "notes": (
                    f"Persistence sentinel observed during {phase}."
                    if observed
                    else f"Persistence sentinel mismatch during {phase}."
                ),
            },
            actor_id=actor_id,
            utc_now=utc_now,
        )
    return dict(
        _row(
            conn,
            """SELECT * FROM staging_persistence_observations
               WHERE observation_id=?""",
            (observation_id,),
            "Persistence observation not found.",
        )
    )


def sync_contact_ledger(
    conn: sqlite3.Connection,
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    inserted = 0
    updated = 0
    now = utc_now()

    access_rows = conn.execute(
        """SELECT request_id, relationship_type, full_name, email,
                  organization, consent_contact, consent_updates,
                  status, message, created_at
           FROM access_requests"""
    ).fetchall()
    for row in access_rows:
        existing = conn.execute(
            """SELECT contact_id FROM beta_contacts
               WHERE source_type='access_request'
                 AND (source_id=? OR email=?)
               ORDER BY updated_at DESC LIMIT 1""",
            (row["request_id"], row["email"]),
        ).fetchone()
        mapped_status = {
            "new": "new",
            "reviewing": "contacted",
            "approved": "pilot_candidate",
            "declined": "declined",
            "archived": "closed",
        }.get(row["status"], "new")
        if existing:
            conn.execute(
                """UPDATE beta_contacts
                   SET source_id=?, full_name=?, email=?, organization=?,
                       relationship_type=?, status=?,
                       consent_contact=?, consent_updates=?,
                       notes=?, updated_at=?
                   WHERE contact_id=?""",
                (
                    row["request_id"],
                    row["full_name"],
                    row["email"],
                    row["organization"],
                    row["relationship_type"],
                    mapped_status,
                    row["consent_contact"],
                    row["consent_updates"],
                    row["message"] or "",
                    now,
                    existing["contact_id"],
                ),
            )
            updated += 1
        else:
            conn.execute(
                """INSERT INTO beta_contacts(
                    contact_id, source_type, source_id, full_name,
                    email, organization, relationship_type, status,
                    owner_id, next_action_at, consent_contact,
                    consent_updates, notes, created_at, updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,NULL,?,?,?,?,?)""",
                (
                    _new_id("CONTACT"),
                    "access_request",
                    row["request_id"],
                    row["full_name"],
                    row["email"],
                    row["organization"],
                    row["relationship_type"],
                    mapped_status,
                    actor_id,
                    row["consent_contact"],
                    row["consent_updates"],
                    row["message"] or "",
                    row["created_at"],
                    now,
                ),
            )
            inserted += 1

    reservation_rows = conn.execute(
        """SELECT reservation_id, email, full_name, status,
                  notes, created_at
           FROM beta_reservations"""
    ).fetchall()
    for row in reservation_rows:
        existing = conn.execute(
            """SELECT contact_id FROM beta_contacts
               WHERE source_type='beta_reservation'
                 AND (source_id=? OR email=?)
               ORDER BY updated_at DESC LIMIT 1""",
            (row["reservation_id"], row["email"]),
        ).fetchone()
        mapped_status = {
            "interest_recorded": "new",
            "contacted": "contacted",
            "approved": "pilot_candidate",
            "declined": "declined",
            "archived": "closed",
        }.get(row["status"], "new")
        if existing:
            conn.execute(
                """UPDATE beta_contacts
                   SET source_id=?, full_name=?, email=?,
                       relationship_type='beta_tester',
                       status=?, notes=?, updated_at=?
                   WHERE contact_id=?""",
                (
                    row["reservation_id"],
                    row["full_name"],
                    row["email"],
                    mapped_status,
                    row["notes"] or "",
                    now,
                    existing["contact_id"],
                ),
            )
            updated += 1
        else:
            conn.execute(
                """INSERT INTO beta_contacts(
                    contact_id, source_type, source_id, full_name,
                    email, organization, relationship_type, status,
                    owner_id, next_action_at, consent_contact,
                    consent_updates, notes, created_at, updated_at
                ) VALUES(?,?,?,?,?,NULL,'beta_tester',?,?,NULL,1,0,?,?,?)""",
                (
                    _new_id("CONTACT"),
                    "beta_reservation",
                    row["reservation_id"],
                    row["full_name"],
                    row["email"],
                    mapped_status,
                    actor_id,
                    row["notes"] or "",
                    row["created_at"],
                    now,
                ),
            )
            inserted += 1

    return {
        "inserted": inserted,
        "updated": updated,
        "total": conn.execute(
            "SELECT COUNT(*) AS n FROM beta_contacts"
        ).fetchone()["n"],
    }


def create_manual_contact(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    full_name = str(payload.get("full_name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    relationship = str(
        payload.get("relationship_type", "beta_tester")
    ).strip()
    if len(full_name) < 2:
        raise ValueError("Contact full name is required.")
    if "@" not in email:
        raise ValueError("A valid contact email is required.")
    contact_id = _new_id("CONTACT")
    now = utc_now()
    conn.execute(
        """INSERT INTO beta_contacts(
            contact_id, source_type, source_id, full_name, email,
            organization, relationship_type, status, owner_id,
            next_action_at, consent_contact, consent_updates, notes,
            created_at, updated_at
        ) VALUES(?,'manual',NULL,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            contact_id,
            full_name,
            email,
            str(payload.get("organization", "")).strip() or None,
            relationship,
            str(payload.get("status", "new")).strip(),
            actor_id,
            str(payload.get("next_action_at", "")).strip() or None,
            1 if payload.get("consent_contact", True) else 0,
            1 if payload.get("consent_updates", False) else 0,
            str(payload.get("notes", "")).strip(),
            now,
            now,
        ),
    )
    return dict(
        _row(
            conn,
            "SELECT * FROM beta_contacts WHERE contact_id=?",
            (contact_id,),
            "Beta contact not found.",
        )
    )


def update_contact(
    conn: sqlite3.Connection,
    contact_id: str,
    payload: dict[str, Any],
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    contact = _row(
        conn,
        "SELECT * FROM beta_contacts WHERE contact_id=?",
        (contact_id,),
        "Beta contact not found.",
    )
    status = str(payload.get("status", contact["status"])).strip()
    allowed = {
        "new",
        "contacted",
        "interview_scheduled",
        "interviewed",
        "pilot_candidate",
        "pilot_active",
        "declined",
        "closed",
    }
    if status not in allowed:
        raise ValueError("A valid beta-contact status is required.")
    conn.execute(
        """UPDATE beta_contacts
           SET status=?, owner_id=?, next_action_at=?, notes=?,
               updated_at=?
           WHERE contact_id=?""",
        (
            status,
            str(payload.get("owner_id", actor_id)).strip() or actor_id,
            str(payload.get("next_action_at", "")).strip() or None,
            str(payload.get("notes", contact["notes"] or "")).strip(),
            utc_now(),
            contact_id,
        ),
    )
    return dict(
        _row(
            conn,
            "SELECT * FROM beta_contacts WHERE contact_id=?",
            (contact_id,),
            "Beta contact not found.",
        )
    )


def create_interview(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    contact_id = str(payload.get("contact_id", "")).strip()
    _row(
        conn,
        "SELECT 1 FROM beta_contacts WHERE contact_id=?",
        (contact_id,),
        "Beta contact not found.",
    )
    interview_type = str(
        payload.get("interview_type", "discovery")
    ).strip()
    if interview_type not in {
        "discovery",
        "pilot_readiness",
        "usability",
        "post_pilot",
    }:
        raise ValueError("A valid interview type is required.")
    interview_id = _new_id("INTERVIEW")
    now = utc_now()
    conn.execute(
        """INSERT INTO beta_interviews(
            interview_id, contact_id, interview_type, scheduled_at,
            completed_at, interviewer_id, goals, pains,
            current_workflow, success_criteria, risk_notes, decision,
            created_at, updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            interview_id,
            contact_id,
            interview_type,
            str(payload.get("scheduled_at", "")).strip() or None,
            str(payload.get("completed_at", "")).strip() or None,
            actor_id,
            str(payload.get("goals", "")).strip(),
            str(payload.get("pains", "")).strip(),
            str(payload.get("current_workflow", "")).strip(),
            str(payload.get("success_criteria", "")).strip(),
            str(payload.get("risk_notes", "")).strip(),
            str(payload.get("decision", "pending")).strip(),
            now,
            now,
        ),
    )
    conn.execute(
        """UPDATE beta_contacts
           SET status=?, updated_at=?
           WHERE contact_id=?""",
        (
            "interviewed"
            if payload.get("completed_at")
            else "interview_scheduled",
            now,
            contact_id,
        ),
    )
    return dict(
        _row(
            conn,
            "SELECT * FROM beta_interviews WHERE interview_id=?",
            (interview_id,),
            "Beta interview not found.",
        )
    )


def create_pilot_record(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    contact_id = str(payload.get("contact_id", "")).strip()
    _row(
        conn,
        "SELECT 1 FROM beta_contacts WHERE contact_id=?",
        (contact_id,),
        "Beta contact not found.",
    )
    manual_workflow = str(payload.get("manual_workflow", "")).strip()
    proposed_scope = str(payload.get("proposed_scope", "")).strip()
    exclusion_scope = str(payload.get("exclusion_scope", "")).strip()
    if not manual_workflow:
        raise ValueError("The current manual workflow is required.")
    if not proposed_scope:
        raise ValueError("A proposed pilot scope is required.")
    if not exclusion_scope:
        raise ValueError("A pilot exclusion scope is required.")
    pilot_id = _new_id("PILOT")
    now = utc_now()
    conn.execute(
        """INSERT INTO pilot_discovery_records(
            pilot_id, contact_id, site_type, location_region,
            manual_workflow, available_infrastructure, data_sources,
            constraints, proposed_scope, exclusion_scope, status,
            approved_by, approved_at, created_by, created_at, updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,'draft',NULL,NULL,?,?,?)""",
        (
            pilot_id,
            contact_id,
            str(payload.get("site_type", "unknown")).strip(),
            str(payload.get("location_region", "")).strip() or None,
            manual_workflow,
            str(payload.get("available_infrastructure", "")).strip(),
            str(payload.get("data_sources", "")).strip(),
            str(payload.get("constraints", "")).strip(),
            proposed_scope,
            exclusion_scope,
            actor_id,
            now,
            now,
        ),
    )
    return dict(
        _row(
            conn,
            "SELECT * FROM pilot_discovery_records WHERE pilot_id=?",
            (pilot_id,),
            "Pilot discovery record not found.",
        )
    )


def review_access_request(
    conn: sqlite3.Connection,
    request_id: str,
    status: str,
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    if status not in {"reviewing", "approved", "declined", "archived"}:
        raise ValueError("A valid access-request review status is required.")
    _row(
        conn,
        "SELECT 1 FROM access_requests WHERE request_id=?",
        (request_id,),
        "Access request not found.",
    )
    conn.execute(
        """UPDATE access_requests
           SET status=?, reviewed_by=?, reviewed_at=?
           WHERE request_id=?""",
        (status, actor_id, utc_now(), request_id),
    )
    sync_contact_ledger(conn, actor_id=actor_id, utc_now=utc_now)
    return dict(
        _row(
            conn,
            "SELECT * FROM access_requests WHERE request_id=?",
            (request_id,),
            "Access request not found.",
        )
    )


def review_beta_reservation(
    conn: sqlite3.Connection,
    reservation_id: str,
    status: str,
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    if status not in {
        "interest_recorded",
        "contacted",
        "approved",
        "declined",
        "archived",
    }:
        raise ValueError("A valid beta-reservation review status is required.")
    _row(
        conn,
        "SELECT 1 FROM beta_reservations WHERE reservation_id=?",
        (reservation_id,),
        "Beta reservation not found.",
    )
    conn.execute(
        "UPDATE beta_reservations SET status=? WHERE reservation_id=?",
        (status, reservation_id),
    )
    sync_contact_ledger(conn, actor_id=actor_id, utc_now=utc_now)
    return dict(
        _row(
            conn,
            "SELECT * FROM beta_reservations WHERE reservation_id=?",
            (reservation_id,),
            "Beta reservation not found.",
        )
    )


def create_claim(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    actor_id: str,
    actor_role: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    claim_text = str(payload.get("claim_text", "")).strip()
    limitations = str(payload.get("limitations", "")).strip()
    if not claim_text:
        raise ValueError("Claim text is required.")
    if not limitations:
        raise ValueError("Claim limitations are required.")
    claim_type = str(payload.get("claim_type", "product")).strip()
    evidence_level = str(payload.get("evidence_level", "prototype")).strip()
    status = str(payload.get("status", "draft")).strip()
    if claim_type not in {
        "product",
        "research",
        "quantum",
        "agricultural",
        "security",
        "operational",
    }:
        raise ValueError("A valid claim type is required.")
    if evidence_level not in {
        "idea",
        "prototype",
        "simulation",
        "controlled_beta",
        "field_verified",
        "publication",
    }:
        raise ValueError("A valid evidence level is required.")
    if status not in {"draft", "approved", "restricted", "rejected", "retired"}:
        raise ValueError("A valid claim status is required.")
    if status == "approved" and actor_role != "administrator":
        raise PermissionError("Only an administrator can approve a claim.")
    if (
        claim_type in {"quantum", "agricultural", "operational"}
        and evidence_level in {"idea", "prototype", "simulation"}
        and status == "approved"
    ):
        raise ValueError(
            "Early-stage quantum, agricultural, and operational claims "
            "cannot be approved without controlled-beta or stronger evidence."
        )
    claim_id = _new_id("CLAIM")
    now = utc_now()
    conn.execute(
        """INSERT INTO claims_register(
            claim_id, claim_text, claim_type, evidence_level, status,
            evidence_reference, limitations, approved_by, approved_at,
            created_by, created_at, updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            claim_id,
            claim_text,
            claim_type,
            evidence_level,
            status,
            str(payload.get("evidence_reference", "")).strip() or None,
            limitations,
            actor_id if status == "approved" else None,
            now if status == "approved" else None,
            actor_id,
            now,
            now,
        ),
    )
    return dict(
        _row(
            conn,
            "SELECT * FROM claims_register WHERE claim_id=?",
            (claim_id,),
            "Claim not found.",
        )
    )


def review_claim(
    conn: sqlite3.Connection,
    claim_id: str,
    payload: dict[str, Any],
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    claim = _row(
        conn,
        "SELECT * FROM claims_register WHERE claim_id=?",
        (claim_id,),
        "Claim not found.",
    )
    status = str(payload.get("status", "")).strip()
    if status not in {"approved", "restricted", "rejected", "retired"}:
        raise ValueError("A valid claim-review decision is required.")
    evidence_level = str(
        payload.get("evidence_level", claim["evidence_level"])
    ).strip()
    limitations = str(
        payload.get("limitations", claim["limitations"])
    ).strip()
    if status == "approved" and (
        claim["claim_type"] in {"quantum", "agricultural", "operational"}
        and evidence_level in {"idea", "prototype", "simulation"}
    ):
        raise ValueError(
            "This claim requires controlled-beta or stronger evidence "
            "before approval."
        )
    now = utc_now()
    conn.execute(
        """UPDATE claims_register
           SET status=?, evidence_level=?, evidence_reference=?,
               limitations=?, approved_by=?, approved_at=?, updated_at=?
           WHERE claim_id=?""",
        (
            status,
            evidence_level,
            str(
                payload.get(
                    "evidence_reference",
                    claim["evidence_reference"] or "",
                )
            ).strip()
            or None,
            limitations,
            actor_id if status == "approved" else None,
            now if status == "approved" else None,
            now,
            claim_id,
        ),
    )
    return dict(
        _row(
            conn,
            "SELECT * FROM claims_register WHERE claim_id=?",
            (claim_id,),
            "Claim not found.",
        )
    )


def update_demo_evidence(
    conn: sqlite3.Connection,
    candidate_id: str,
    payload: dict[str, Any],
    *,
    actor_id: str,
    actor_role: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    evidence_code = str(payload.get("evidence_code", "")).strip()
    item = _row(
        conn,
        """SELECT * FROM demo_evidence_items
           WHERE candidate_id=? AND evidence_code=?""",
        (candidate_id, evidence_code),
        "Demo evidence item not found.",
    )
    status = str(payload.get("status", item["status"])).strip()
    if status not in {"missing", "captured", "verified", "rejected"}:
        raise ValueError("A valid demo-evidence status is required.")
    if status in {"verified", "rejected"} and actor_role != "administrator":
        raise PermissionError(
            "Only an administrator can verify or reject demo evidence."
        )
    file_reference = str(
        payload.get("file_reference", item["file_reference"] or "")
    ).strip() or None
    digest = str(payload.get("sha256", item["sha256"] or "")).strip() or None
    if status in {"captured", "verified"} and not file_reference:
        raise ValueError("A file or evidence reference is required.")
    now = utc_now()
    conn.execute(
        """UPDATE demo_evidence_items
           SET status=?, file_reference=?, sha256=?, notes=?,
               captured_at=?, verified_by=?, verified_at=?
           WHERE item_id=?""",
        (
            status,
            file_reference,
            digest,
            str(payload.get("notes", item["notes"] or "")).strip(),
            now if status in {"captured", "verified"} else item["captured_at"],
            actor_id if status == "verified" else None,
            now if status == "verified" else None,
            item["item_id"],
        ),
    )
    return dict(
        _row(
            conn,
            "SELECT * FROM demo_evidence_items WHERE item_id=?",
            (item["item_id"],),
            "Demo evidence item not found.",
        )
    )


def create_yc_update(
    conn: sqlite3.Connection,
    candidate_id: str,
    payload: dict[str, Any],
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    _candidate_row(conn, candidate_id)
    headline = str(payload.get("headline", "")).strip()
    summary = str(payload.get("summary", "")).strip()
    limitations = str(payload.get("limitations", "")).strip()
    if not headline or not summary or not limitations:
        raise ValueError(
            "YC update headline, summary, and limitations are required."
        )
    metrics = payload.get("metrics") or {}
    if not isinstance(metrics, dict):
        raise ValueError("YC update metrics must be an object.")
    evidence = {
        row["evidence_code"]: {
            "status": row["status"],
            "file_reference": row["file_reference"],
            "sha256": row["sha256"],
        }
        for row in conn.execute(
            """SELECT evidence_code, status, file_reference, sha256
               FROM demo_evidence_items WHERE candidate_id=?""",
            (candidate_id,),
        ).fetchall()
    }
    update_id = _new_id("YCUPDATE")
    conn.execute(
        """INSERT INTO yc_update_snapshots(
            update_id, candidate_id, headline, summary, metrics_json,
            limitations, evidence_manifest_json, created_by, created_at
        ) VALUES(?,?,?,?,?,?,?,?,?)""",
        (
            update_id,
            candidate_id,
            headline,
            summary,
            canonical_json(metrics),
            limitations,
            canonical_json(evidence),
            actor_id,
            utc_now(),
        ),
    )
    row = _row(
        conn,
        "SELECT * FROM yc_update_snapshots WHERE update_id=?",
        (update_id,),
        "YC update snapshot not found.",
    )
    result = dict(row)
    result["metrics"] = _json_load(result.pop("metrics_json"), {})
    result["evidence_manifest"] = _json_load(
        result.pop("evidence_manifest_json"),
        {},
    )
    return result


def _latest_failed_validations(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "quantum_validation_events" not in tables:
        return []
    return [
        dict(row)
        for row in conn.execute(
            """WITH ranked AS (
                   SELECT validation_id, run_id, gate_type, status,
                          message, created_at,
                          ROW_NUMBER() OVER (
                              PARTITION BY run_id, gate_type
                              ORDER BY created_at DESC, validation_id DESC
                          ) AS rn
                   FROM quantum_validation_events
                   WHERE run_id IS NOT NULL
               )
               SELECT validation_id, run_id, gate_type, status,
                      message, created_at
               FROM ranked
               WHERE rn=1 AND status='failed'
               ORDER BY created_at DESC"""
        ).fetchall()
    ]


def _acceptance_blockers(
    conn: sqlite3.Connection,
    candidate_id: str,
) -> dict[str, Any]:
    candidate = _candidate_row(conn, candidate_id)
    check_blockers = [
        dict(row)
        for row in conn.execute(
            """SELECT check_code, category, status, notes
               FROM staging_acceptance_checks
               WHERE candidate_id=?
                 AND status NOT IN ('passed','not_applicable')
               ORDER BY category, check_code""",
            (candidate_id,),
        ).fetchall()
    ]
    evidence_blockers = [
        dict(row)
        for row in conn.execute(
            """SELECT evidence_code, title, status
               FROM demo_evidence_items
               WHERE candidate_id=? AND status<>'verified'
               ORDER BY evidence_code""",
            (candidate_id,),
        ).fetchall()
    ]
    latest_backup = conn.execute(
        """SELECT backup_id, filename, status, verified_at
           FROM backup_runs
           ORDER BY created_at DESC LIMIT 1"""
    ).fetchone()
    backup_blocker = (
        None
        if latest_backup and latest_backup["status"] == "verified"
        else "No verified database backup is recorded."
    )
    failed_validations = _latest_failed_validations(conn)
    rollback = conn.execute(
        """SELECT status FROM staging_acceptance_checks
           WHERE candidate_id=? AND check_code='rollback_checkpoint'""",
        (candidate_id,),
    ).fetchone()
    release_boundary = conn.execute(
        """SELECT status FROM staging_acceptance_checks
           WHERE candidate_id=? AND check_code='manual_release_boundary'""",
        (candidate_id,),
    ).fetchone()
    candidate_status_blocker = (
        None
        if candidate["status"] in {"deployed", "verifying", "accepted"}
        else "The staging candidate has not reached deployed or verifying status."
    )
    return {
        "candidate_status": candidate["status"],
        "candidate_status_blocker": candidate_status_blocker,
        "check_blockers": check_blockers,
        "evidence_blockers": evidence_blockers,
        "backup_blocker": backup_blocker,
        "failed_validations": failed_validations,
        "rollback_checkpoint_passed": bool(
            rollback and rollback["status"] == "passed"
        ),
        "manual_release_boundary_passed": bool(
            release_boundary and release_boundary["status"] == "passed"
        ),
        "blocked": bool(
            candidate_status_blocker
            or check_blockers
            or evidence_blockers
            or backup_blocker
            or failed_validations
        ),
    }


def decide_staging_candidate(
    conn: sqlite3.Connection,
    candidate_id: str,
    payload: dict[str, Any],
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    candidate = _candidate_row(conn, candidate_id)
    decision = str(payload.get("decision", "")).strip()
    reason = str(payload.get("reason", "")).strip()
    if decision not in {"accepted", "rejected"}:
        raise ValueError("Decision must be accepted or rejected.")
    if not reason:
        raise ValueError("A staging acceptance decision requires a reason.")
    blockers = _acceptance_blockers(conn, candidate_id)
    if decision == "accepted" and blockers["blocked"]:
        raise ValueError(
            "Staging acceptance remains blocked until every required "
            "check, evidence item, backup, and scientific gate passes."
        )
    now = utc_now()
    decision_id = _new_id("STAGEDEC")
    conn.execute(
        """INSERT INTO staging_acceptance_decisions(
            decision_id, candidate_id, decision, reason,
            blocker_summary_json, decided_by, decided_at
        ) VALUES(?,?,?,?,?,?,?)""",
        (
            decision_id,
            candidate_id,
            decision,
            reason,
            canonical_json(blockers),
            actor_id,
            now,
        ),
    )
    conn.execute(
        """UPDATE staging_candidates
           SET status=?, accepted_by=?, accepted_at=?, updated_at=?
           WHERE candidate_id=?""",
        (
            decision,
            actor_id if decision == "accepted" else None,
            now if decision == "accepted" else None,
            now,
            candidate_id,
        ),
    )
    return _serialize_candidate(
        conn,
        _candidate_row(conn, candidate_id),
    )


def _json_file(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            default=str,
        )
        + "\n"
    ).encode("utf-8")


def _deterministic_zip(files: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(
        output,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for filename in sorted(files):
            info = zipfile.ZipInfo(filename)
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, files[filename])
    return output.getvalue()


def build_controlled_beta_export(
    conn: sqlite3.Connection,
    candidate_id: str,
) -> tuple[bytes, dict[str, Any]]:
    candidate = _serialize_candidate(
        conn,
        _candidate_row(conn, candidate_id),
    )
    contacts = [
        dict(row)
        for row in conn.execute(
            "SELECT * FROM beta_contacts ORDER BY created_at, contact_id"
        ).fetchall()
    ]
    interviews = [
        dict(row)
        for row in conn.execute(
            "SELECT * FROM beta_interviews ORDER BY created_at, interview_id"
        ).fetchall()
    ]
    pilots = [
        dict(row)
        for row in conn.execute(
            """SELECT * FROM pilot_discovery_records
               ORDER BY created_at, pilot_id"""
        ).fetchall()
    ]
    claims = [
        dict(row)
        for row in conn.execute(
            "SELECT * FROM claims_register ORDER BY created_at, claim_id"
        ).fetchall()
    ]
    policies = []
    for row in conn.execute(
        """SELECT * FROM invitation_policies
           ORDER BY created_at, policy_id"""
    ).fetchall():
        item = dict(row)
        item["policy"] = _json_load(item.pop("policy_json"), {})
        policies.append(item)
    access_requests = [
        dict(row)
        for row in conn.execute(
            """SELECT * FROM access_requests
               ORDER BY created_at, request_id"""
        ).fetchall()
    ]
    reservations = [
        dict(row)
        for row in conn.execute(
            """SELECT * FROM beta_reservations
               ORDER BY created_at, reservation_id"""
        ).fetchall()
    ]
    blockers = _acceptance_blockers(conn, candidate_id)

    files = {
        "README.md": (
            "# AgroQ Controlled Beta Evidence\n\n"
            f"Candidate: {candidate_id}\n\n"
            "This package records staging acceptance, persistence "
            "verification, demo evidence, beta-contact operations, "
            "pilot discovery, invitation policy, claims controls, "
            "YC update snapshots, and explicit limitations.\n"
        ).encode("utf-8"),
        "staging_candidate.json": _json_file(candidate),
        "acceptance_blockers.json": _json_file(blockers),
        "contact_ledger.json": _json_file(contacts),
        "user_interviews.json": _json_file(interviews),
        "pilot_discovery.json": _json_file(pilots),
        "claims_register.json": _json_file(claims),
        "invitation_policies.json": _json_file(policies),
        "access_requests.json": _json_file(access_requests),
        "beta_reservations.json": _json_file(reservations),
    }
    hashes = {
        name: hashlib.sha256(content).hexdigest()
        for name, content in sorted(files.items())
    }
    files["SHA256SUMS.txt"] = "".join(
        f"{digest}  {name}\n"
        for name, digest in hashes.items()
    ).encode("utf-8")
    bundle = _deterministic_zip(files)
    manifest = {
        "schema_version": Q17_Q19_SCHEMA_VERSION,
        "candidate_id": candidate_id,
        "file_count": len(files),
        "files": {
            name: hashlib.sha256(content).hexdigest()
            for name, content in sorted(files.items())
        },
        "bundle_sha256": hashlib.sha256(bundle).hexdigest(),
    }
    return bundle, manifest


def store_controlled_beta_export(
    conn: sqlite3.Connection,
    candidate_id: str,
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> tuple[bytes, dict[str, Any]]:
    bundle, manifest = build_controlled_beta_export(conn, candidate_id)
    export_id = _new_id("BETAEXPORT")
    filename = f"{candidate_id.lower()}-controlled-beta-evidence.zip"
    conn.execute(
        """INSERT INTO controlled_beta_exports(
            export_id, candidate_id, filename, sha256,
            manifest_json, created_by, created_at
        ) VALUES(?,?,?,?,?,?,?)""",
        (
            export_id,
            candidate_id,
            filename,
            manifest["bundle_sha256"],
            canonical_json(manifest),
            actor_id,
            utc_now(),
        ),
    )
    return bundle, {
        "export_id": export_id,
        "filename": filename,
        **manifest,
    }


def controlled_beta_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    candidates = [
        _serialize_candidate(conn, row, include_details=False)
        for row in conn.execute(
            """SELECT * FROM staging_candidates
               ORDER BY updated_at DESC"""
        ).fetchall()
    ]
    contact_counts = {
        row["status"]: row["n"]
        for row in conn.execute(
            """SELECT status, COUNT(*) AS n
               FROM beta_contacts GROUP BY status"""
        ).fetchall()
    }
    claim_counts = {
        row["status"]: row["n"]
        for row in conn.execute(
            """SELECT status, COUNT(*) AS n
               FROM claims_register GROUP BY status"""
        ).fetchall()
    }
    active_policy = conn.execute(
        """SELECT * FROM invitation_policies
           WHERE active=1 ORDER BY created_at DESC LIMIT 1"""
    ).fetchone()
    policy = None
    if active_policy:
        policy = dict(active_policy)
        policy["policy"] = _json_load(policy.pop("policy_json"), {})
    return {
        "schema_version": Q17_Q19_SCHEMA_VERSION,
        "candidates": candidates,
        "contacts": [
            dict(row)
            for row in conn.execute(
                """SELECT * FROM beta_contacts
                   ORDER BY updated_at DESC LIMIT 200"""
            ).fetchall()
        ],
        "contact_counts": contact_counts,
        "interviews": [
            dict(row)
            for row in conn.execute(
                """SELECT * FROM beta_interviews
                   ORDER BY updated_at DESC LIMIT 200"""
            ).fetchall()
        ],
        "pilots": [
            dict(row)
            for row in conn.execute(
                """SELECT * FROM pilot_discovery_records
                   ORDER BY updated_at DESC LIMIT 200"""
            ).fetchall()
        ],
        "claims": [
            dict(row)
            for row in conn.execute(
                """SELECT * FROM claims_register
                   ORDER BY updated_at DESC LIMIT 200"""
            ).fetchall()
        ],
        "claim_counts": claim_counts,
        "active_invitation_policy": policy,
        "access_requests": [
            dict(row)
            for row in conn.execute(
                """SELECT * FROM access_requests
                   ORDER BY created_at DESC LIMIT 100"""
            ).fetchall()
        ],
        "beta_reservations": [
            dict(row)
            for row in conn.execute(
                """SELECT * FROM beta_reservations
                   ORDER BY created_at DESC LIMIT 100"""
            ).fetchall()
        ],
    }


def register_controlled_beta(
    *,
    app: Any,
    get_db: Callable[[], Any],
    utc_now: Callable[[], str],
    record_audit_event: Callable[..., None],
    roles_required: Callable[..., Any],
) -> None:
    from flask import Blueprint, Response, g, jsonify, request

    blueprint = Blueprint("controlled_beta", __name__)

    @app.before_request
    def ensure_controlled_beta_tables() -> None:
        with get_db() as conn:
            ensure_controlled_beta_schema(conn)

    def audit(
        action: str,
        entity_type: str,
        entity_id: str,
        details: dict[str, Any],
    ) -> None:
        record_audit_event(
            g.user["user_id"] if g.user else None,
            action,
            entity_type,
            entity_id,
            canonical_json(details),
        )

    @blueprint.get("/api/beta/operations/summary")
    @roles_required(*VIEW_ROLES)
    def beta_operations_summary() -> Response:
        with get_db() as conn:
            ensure_controlled_beta_schema(
                conn,
                created_by=g.user["user_id"],
                utc_now=utc_now,
            )
            payload = controlled_beta_summary(conn)
        return jsonify({"ok": True, **payload})

    @blueprint.post("/api/beta/staging-candidates")
    @roles_required(*ADMIN_ROLES)
    def api_create_staging_candidate() -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        try:
            with get_db() as conn:
                candidate = create_staging_candidate(
                    conn,
                    payload,
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except (ValueError, sqlite3.IntegrityError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "controlled_beta_candidate_created",
            "staging_candidate",
            candidate["candidate_id"],
            {
                "commit_sha": candidate["commit_sha"],
                "release_tag": candidate["release_tag"],
            },
        )
        return jsonify({"ok": True, "candidate": candidate}), 201

    @blueprint.get("/api/beta/staging-candidates/<candidate_id>")
    @roles_required(*VIEW_ROLES)
    def api_staging_candidate_detail(
        candidate_id: str,
    ) -> tuple[Response, int] | Response:
        try:
            with get_db() as conn:
                candidate = _serialize_candidate(
                    conn,
                    _candidate_row(conn, candidate_id),
                )
                blockers = _acceptance_blockers(conn, candidate_id)
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 404
        return jsonify(
            {
                "ok": True,
                "candidate": candidate,
                "acceptance_blockers": blockers,
            }
        )

    @blueprint.post("/api/beta/staging-candidates/<candidate_id>/deployment")
    @roles_required(*ADMIN_ROLES)
    def api_update_candidate_deployment(
        candidate_id: str,
    ) -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        try:
            with get_db() as conn:
                candidate = update_candidate_deployment(
                    conn,
                    candidate_id,
                    payload,
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "controlled_beta_deployment_updated",
            "staging_candidate",
            candidate_id,
            {
                "status": candidate["status"],
                "service_id": candidate["service_id"],
            },
        )
        return jsonify({"ok": True, "candidate": candidate})

    @blueprint.post("/api/beta/staging-candidates/<candidate_id>/checks")
    @roles_required(*OPERATIONS_ROLES)
    def api_record_candidate_check(
        candidate_id: str,
    ) -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        try:
            with get_db() as conn:
                check = record_acceptance_check(
                    conn,
                    candidate_id,
                    payload,
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "controlled_beta_acceptance_check_recorded",
            "staging_candidate",
            candidate_id,
            {
                "check_code": check["check_code"],
                "status": check["status"],
            },
        )
        return jsonify({"ok": True, "check": check})

    @blueprint.post("/api/beta/staging-candidates/<candidate_id>/sentinels")
    @roles_required(*ADMIN_ROLES)
    def api_create_sentinel(
        candidate_id: str,
    ) -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        try:
            with get_db() as conn:
                sentinel = create_persistence_sentinel(
                    conn,
                    candidate_id,
                    payload,
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except (ValueError, sqlite3.IntegrityError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "controlled_beta_persistence_sentinel_created",
            "staging_candidate",
            candidate_id,
            {"sentinel_id": sentinel["sentinel_id"]},
        )
        return jsonify({"ok": True, "sentinel": sentinel}), 201

    @blueprint.post(
        "/api/beta/staging-candidates/<candidate_id>/sentinels/<sentinel_id>/observe"
    )
    @roles_required(*ADMIN_ROLES)
    def api_observe_sentinel(
        candidate_id: str,
        sentinel_id: str,
    ) -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        try:
            with get_db() as conn:
                observation = observe_persistence_sentinel(
                    conn,
                    candidate_id,
                    sentinel_id,
                    payload,
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "controlled_beta_persistence_observed",
            "staging_candidate",
            candidate_id,
            {
                "sentinel_id": sentinel_id,
                "phase": observation["phase"],
                "observed": bool(observation["observed"]),
            },
        )
        return jsonify({"ok": True, "observation": observation})

    @blueprint.post("/api/beta/staging-candidates/<candidate_id>/decision")
    @roles_required(*ADMIN_ROLES)
    def api_decide_candidate(
        candidate_id: str,
    ) -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        try:
            with get_db() as conn:
                candidate = decide_staging_candidate(
                    conn,
                    candidate_id,
                    payload,
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 409
        audit(
            "controlled_beta_staging_decision",
            "staging_candidate",
            candidate_id,
            {"decision": candidate["status"]},
        )
        return jsonify({"ok": True, "candidate": candidate})

    @blueprint.post("/api/beta/contacts/sync")
    @roles_required(*OPERATIONS_ROLES)
    def api_sync_contacts() -> Response:
        with get_db() as conn:
            result = sync_contact_ledger(
                conn,
                actor_id=g.user["user_id"],
                utc_now=utc_now,
            )
        audit(
            "controlled_beta_contacts_synced",
            "beta_contact",
            "ledger",
            result,
        )
        return jsonify({"ok": True, "sync": result})

    @blueprint.post("/api/beta/contacts")
    @roles_required(*OPERATIONS_ROLES)
    def api_create_contact() -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        try:
            with get_db() as conn:
                contact = create_manual_contact(
                    conn,
                    payload,
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except (ValueError, sqlite3.IntegrityError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "controlled_beta_contact_created",
            "beta_contact",
            contact["contact_id"],
            {"email": contact["email"], "status": contact["status"]},
        )
        return jsonify({"ok": True, "contact": contact}), 201

    @blueprint.patch("/api/beta/contacts/<contact_id>")
    @roles_required(*OPERATIONS_ROLES)
    def api_update_contact(
        contact_id: str,
    ) -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        try:
            with get_db() as conn:
                contact = update_contact(
                    conn,
                    contact_id,
                    payload,
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "controlled_beta_contact_updated",
            "beta_contact",
            contact_id,
            {"status": contact["status"]},
        )
        return jsonify({"ok": True, "contact": contact})

    @blueprint.post("/api/beta/interviews")
    @roles_required(*OPERATIONS_ROLES)
    def api_create_interview() -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        try:
            with get_db() as conn:
                interview = create_interview(
                    conn,
                    payload,
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except (ValueError, sqlite3.IntegrityError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "controlled_beta_interview_recorded",
            "beta_interview",
            interview["interview_id"],
            {
                "contact_id": interview["contact_id"],
                "decision": interview["decision"],
            },
        )
        return jsonify({"ok": True, "interview": interview}), 201

    @blueprint.post("/api/beta/pilots")
    @roles_required(*OPERATIONS_ROLES)
    def api_create_pilot() -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        try:
            with get_db() as conn:
                pilot = create_pilot_record(
                    conn,
                    payload,
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except (ValueError, sqlite3.IntegrityError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "controlled_beta_pilot_discovery_created",
            "pilot_discovery",
            pilot["pilot_id"],
            {"contact_id": pilot["contact_id"]},
        )
        return jsonify({"ok": True, "pilot": pilot}), 201

    @blueprint.post("/api/beta/pilots/<pilot_id>/review")
    @roles_required(*ADMIN_ROLES)
    def api_review_pilot(
        pilot_id: str,
    ) -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        status = str(payload.get("status", "")).strip()
        if status not in {"approved", "declined", "completed"}:
            return jsonify(
                {"ok": False, "error": "A valid pilot-review status is required."}
            ), 400
        try:
            with get_db() as conn:
                pilot = _row(
                    conn,
                    """SELECT * FROM pilot_discovery_records
                       WHERE pilot_id=?""",
                    (pilot_id,),
                    "Pilot discovery record not found.",
                )
                if status == "approved" and (
                    not pilot["manual_workflow"]
                    or not pilot["proposed_scope"]
                    or not pilot["exclusion_scope"]
                ):
                    raise ValueError(
                        "Manual workflow, proposed scope, and exclusion scope "
                        "must be documented before pilot approval."
                    )
                now = utc_now()
                conn.execute(
                    """UPDATE pilot_discovery_records
                       SET status=?, approved_by=?, approved_at=?, updated_at=?
                       WHERE pilot_id=?""",
                    (
                        status,
                        g.user["user_id"] if status == "approved" else None,
                        now if status == "approved" else None,
                        now,
                        pilot_id,
                    ),
                )
                result = dict(
                    _row(
                        conn,
                        """SELECT * FROM pilot_discovery_records
                           WHERE pilot_id=?""",
                        (pilot_id,),
                        "Pilot discovery record not found.",
                    )
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "controlled_beta_pilot_reviewed",
            "pilot_discovery",
            pilot_id,
            {"status": status},
        )
        return jsonify({"ok": True, "pilot": result})

    @blueprint.post("/api/beta/claims")
    @roles_required(*OPERATIONS_ROLES)
    def api_create_claim() -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        try:
            with get_db() as conn:
                claim = create_claim(
                    conn,
                    payload,
                    actor_id=g.user["user_id"],
                    actor_role=g.user["role"],
                    utc_now=utc_now,
                )
        except PermissionError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 403
        except (ValueError, sqlite3.IntegrityError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "controlled_beta_claim_created",
            "claim",
            claim["claim_id"],
            {
                "status": claim["status"],
                "evidence_level": claim["evidence_level"],
            },
        )
        return jsonify({"ok": True, "claim": claim}), 201

    @blueprint.post("/api/beta/claims/<claim_id>/review")
    @roles_required(*ADMIN_ROLES)
    def api_review_claim(
        claim_id: str,
    ) -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        try:
            with get_db() as conn:
                claim = review_claim(
                    conn,
                    claim_id,
                    payload,
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "controlled_beta_claim_reviewed",
            "claim",
            claim_id,
            {"status": claim["status"]},
        )
        return jsonify({"ok": True, "claim": claim})

    @blueprint.post("/api/beta/access-requests/<request_id>/review")
    @roles_required(*ADMIN_ROLES)
    def api_review_access_request(
        request_id: str,
    ) -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        try:
            with get_db() as conn:
                result = review_access_request(
                    conn,
                    request_id,
                    str(payload.get("status", "")).strip(),
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "controlled_beta_access_request_reviewed",
            "access_request",
            request_id,
            {"status": result["status"]},
        )
        return jsonify({"ok": True, "access_request": result})

    @blueprint.post("/api/beta/reservations/<reservation_id>/review")
    @roles_required(*ADMIN_ROLES)
    def api_review_reservation(
        reservation_id: str,
    ) -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        try:
            with get_db() as conn:
                result = review_beta_reservation(
                    conn,
                    reservation_id,
                    str(payload.get("status", "")).strip(),
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "controlled_beta_reservation_reviewed",
            "beta_reservation",
            reservation_id,
            {"status": result["status"]},
        )
        return jsonify({"ok": True, "reservation": result})

    @blueprint.post("/api/beta/staging-candidates/<candidate_id>/evidence")
    @roles_required(*OPERATIONS_ROLES)
    def api_update_evidence(
        candidate_id: str,
    ) -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        try:
            with get_db() as conn:
                evidence = update_demo_evidence(
                    conn,
                    candidate_id,
                    payload,
                    actor_id=g.user["user_id"],
                    actor_role=g.user["role"],
                    utc_now=utc_now,
                )
        except PermissionError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 403
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "controlled_beta_demo_evidence_updated",
            "staging_candidate",
            candidate_id,
            {
                "evidence_code": evidence["evidence_code"],
                "status": evidence["status"],
            },
        )
        return jsonify({"ok": True, "evidence": evidence})

    @blueprint.post("/api/beta/staging-candidates/<candidate_id>/yc-update")
    @roles_required(*OPERATIONS_ROLES)
    def api_create_yc_update(
        candidate_id: str,
    ) -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        try:
            with get_db() as conn:
                update = create_yc_update(
                    conn,
                    candidate_id,
                    payload,
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "controlled_beta_yc_update_created",
            "staging_candidate",
            candidate_id,
            {"update_id": update["update_id"]},
        )
        return jsonify({"ok": True, "yc_update": update}), 201

    @blueprint.get("/api/beta/staging-candidates/<candidate_id>/evidence.zip")
    @roles_required(*OPERATIONS_ROLES)
    def api_export_controlled_beta(
        candidate_id: str,
    ) -> tuple[Response, int] | Response:
        try:
            with get_db() as conn:
                bundle, export = store_controlled_beta_export(
                    conn,
                    candidate_id,
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 404
        audit(
            "controlled_beta_evidence_exported",
            "staging_candidate",
            candidate_id,
            {
                "export_id": export["export_id"],
                "sha256": export["bundle_sha256"],
            },
        )
        response = Response(bundle, content_type="application/zip")
        response.headers["Content-Disposition"] = (
            f'attachment; filename="{export["filename"]}"'
        )
        response.headers["X-AgroQ-SHA256"] = export["bundle_sha256"]
        response.headers["X-AgroQ-Export-ID"] = export["export_id"]
        return response

    @blueprint.post("/api/beta/invitation-policy")
    @roles_required(*ADMIN_ROLES)
    def api_update_invitation_policy() -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        policy = {**DEFAULT_INVITATION_POLICY, **payload}
        try:
            max_days = int(policy["max_expiry_days"])
            default_uses = int(policy["default_max_uses"])
            absolute_uses = int(policy["absolute_max_uses"])
        except (TypeError, ValueError):
            return jsonify(
                {"ok": False, "error": "Invitation-policy limits must be integers."}
            ), 400
        if not (1 <= max_days <= 90):
            return jsonify(
                {"ok": False, "error": "max_expiry_days must be between 1 and 90."}
            ), 400
        if not (1 <= default_uses <= absolute_uses <= 25):
            return jsonify(
                {
                    "ok": False,
                    "error": (
                        "Invitation uses must satisfy "
                        "1 <= default_max_uses <= absolute_max_uses <= 25."
                    ),
                }
            ), 400
        version = str(payload.get("version", "")).strip() or (
            f"controlled-beta-{time.time_ns()}"
        )
        now = utc_now()
        with get_db() as conn:
            conn.execute("UPDATE invitation_policies SET active=0 WHERE active=1")
            policy_id = _new_id("INVITEPOL")
            conn.execute(
                """INSERT INTO invitation_policies(
                    policy_id, version, active, policy_json,
                    approved_by, approved_at, created_by, created_at
                ) VALUES(?,?,1,?,?,?,?,?)""",
                (
                    policy_id,
                    version,
                    canonical_json(policy),
                    g.user["user_id"],
                    now,
                    g.user["user_id"],
                    now,
                ),
            )
        audit(
            "controlled_beta_invitation_policy_approved",
            "invitation_policy",
            policy_id,
            {"version": version},
        )
        return jsonify(
            {
                "ok": True,
                "invitation_policy": {
                    "policy_id": policy_id,
                    "version": version,
                    "active": 1,
                    "policy": policy,
                    "approved_by": g.user["user_id"],
                    "approved_at": now,
                },
            }
        ), 201

    app.register_blueprint(blueprint)
