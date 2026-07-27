from __future__ import annotations

import hashlib
import io
import json
import sqlite3
import time
import zipfile
from pathlib import Path
from typing import Any, Callable

from controlled_beta import ensure_controlled_beta_schema

Q20_Q22_SCHEMA_VERSION = "AGROQ-PILOT-OPERATIONS-1.0"
BASE_DIR = Path(__file__).resolve().parent
VIEW_ROLES = ("administrator", "researcher", "field_operator", "viewer")
OPERATIONS_ROLES = ("administrator", "researcher")
ADMIN_ROLES = ("administrator",)

REQUIRED_ONBOARDING_CHECKS: tuple[tuple[str, str], ...] = (
    ("account_access", "Participant account and assigned role verified"),
    ("manual_workflow_training", "Manual-first workflow training completed"),
    ("data_handling", "Data handling and correction workflow reviewed"),
    ("human_control_boundary", "Human-control boundary reviewed"),
    ("support_escalation", "Support and incident escalation path verified"),
    ("success_metrics", "Pilot success metrics defined before activation"),
)
REQUIRED_ACKNOWLEDGMENTS = (
    "data_handling",
    "human_control",
    "research_limitations",
)
SEVERE_INCIDENTS = ("high", "critical")


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


def _new_id(prefix: str) -> str:
    return f"AGQ-{prefix}-{time.time_ns()}"


def _row(
    conn: sqlite3.Connection,
    query: str,
    params: tuple[Any, ...],
    error: str,
) -> sqlite3.Row:
    row = conn.execute(query, params).fetchone()
    if row is None:
        raise ValueError(error)
    return row


def ensure_pilot_operations_schema(conn: sqlite3.Connection) -> None:
    ensure_controlled_beta_schema(conn)
    schema = (BASE_DIR / "pilot_operations_schema.sql").read_text(
        encoding="utf-8"
    )
    conn.executescript(schema)


def _enrollment_row(
    conn: sqlite3.Connection,
    enrollment_id: str,
) -> sqlite3.Row:
    return _row(
        conn,
        "SELECT * FROM pilot_enrollments WHERE enrollment_id=?",
        (enrollment_id,),
        "Pilot enrollment not found.",
    )


def _latest_incident_status(
    conn: sqlite3.Connection,
    incident_id: str,
) -> str:
    return str(
        _row(
            conn,
            """SELECT status FROM pilot_incident_events
               WHERE incident_id=?
               ORDER BY recorded_at DESC, event_id DESC LIMIT 1""",
            (incident_id,),
            "Pilot incident status not found.",
        )["status"]
    )


def _record_status(
    conn: sqlite3.Connection,
    enrollment_id: str,
    new_status: str,
    reason: str,
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    enrollment = _enrollment_row(conn, enrollment_id)
    if new_status not in {
        "draft",
        "onboarding",
        "active",
        "paused",
        "completed",
        "withdrawn",
    }:
        raise ValueError("A valid pilot status is required.")
    reason = reason.strip()
    if not reason:
        raise ValueError("A pilot status reason is required.")
    now = utc_now()
    conn.execute(
        """INSERT INTO pilot_status_events(
            event_id,enrollment_id,previous_status,new_status,
            reason,recorded_by,recorded_at
        ) VALUES(?,?,?,?,?,?,?)""",
        (
            _new_id("PILOTSTATUS"),
            enrollment_id,
            enrollment["status"],
            new_status,
            reason,
            actor_id,
            now,
        ),
    )
    conn.execute(
        """UPDATE pilot_enrollments
           SET status=?, updated_at=? WHERE enrollment_id=?""",
        (new_status, now, enrollment_id),
    )
    return dict(_enrollment_row(conn, enrollment_id))


def serialize_enrollment(
    conn: sqlite3.Connection,
    enrollment_id: str,
) -> dict[str, Any]:
    record = dict(_enrollment_row(conn, enrollment_id))
    record["onboarding_checks"] = [
        dict(row)
        for row in conn.execute(
            """SELECT * FROM pilot_onboarding_checks
               WHERE enrollment_id=? ORDER BY check_code""",
            (enrollment_id,),
        ).fetchall()
    ]
    record["acknowledgments"] = [
        dict(row)
        for row in conn.execute(
            """SELECT * FROM pilot_acknowledgments
               WHERE enrollment_id=?
               ORDER BY acknowledged_at, acknowledgment_type""",
            (enrollment_id,),
        ).fetchall()
    ]
    record["status_events"] = [
        dict(row)
        for row in conn.execute(
            """SELECT * FROM pilot_status_events
               WHERE enrollment_id=?
               ORDER BY recorded_at, event_id""",
            (enrollment_id,),
        ).fetchall()
    ]
    record["feedback"] = []
    for row in conn.execute(
        """SELECT * FROM pilot_feedback
           WHERE enrollment_id=? ORDER BY submitted_at DESC""",
        (enrollment_id,),
    ).fetchall():
        item = dict(row)
        item["reviews"] = [
            dict(review)
            for review in conn.execute(
                """SELECT * FROM pilot_feedback_reviews
                   WHERE feedback_id=?
                   ORDER BY reviewed_at, review_id""",
                (row["feedback_id"],),
            ).fetchall()
        ]
        item["status"] = (
            item["reviews"][-1]["status"] if item["reviews"] else "new"
        )
        record["feedback"].append(item)
    record["incidents"] = []
    for row in conn.execute(
        """SELECT * FROM pilot_incidents
           WHERE enrollment_id=? ORDER BY reported_at DESC""",
        (enrollment_id,),
    ).fetchall():
        item = dict(row)
        item["events"] = [
            dict(event)
            for event in conn.execute(
                """SELECT * FROM pilot_incident_events
                   WHERE incident_id=?
                   ORDER BY recorded_at, event_id""",
                (row["incident_id"],),
            ).fetchall()
        ]
        item["status"] = item["events"][-1]["status"]
        record["incidents"].append(item)
    record["metrics"] = [
        dict(row)
        for row in conn.execute(
            """SELECT * FROM pilot_metric_observations
               WHERE enrollment_id=?
               ORDER BY captured_at DESC, metric_code""",
            (enrollment_id,),
        ).fetchall()
    ]
    record["exit_decisions"] = []
    for row in conn.execute(
        """SELECT * FROM pilot_exit_decisions
           WHERE enrollment_id=?
           ORDER BY decided_at DESC, decision_id DESC""",
        (enrollment_id,),
    ).fetchall():
        item = dict(row)
        item["blocker_summary"] = json.loads(item.pop("blocker_summary_json"))
        record["exit_decisions"].append(item)
    record["activation_blockers"] = activation_blockers(conn, enrollment_id)
    record["release_review_blockers"] = release_review_blockers(
        conn,
        enrollment_id,
    )
    return record


def create_enrollment(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    pilot_id = str(payload.get("pilot_id", "")).strip()
    candidate_id = str(payload.get("candidate_id", "")).strip()
    pilot = _row(
        conn,
        "SELECT * FROM pilot_discovery_records WHERE pilot_id=?",
        (pilot_id,),
        "Approved pilot discovery record not found.",
    )
    candidate = _row(
        conn,
        "SELECT * FROM staging_candidates WHERE candidate_id=?",
        (candidate_id,),
        "Accepted staging candidate not found.",
    )
    if pilot["status"] != "approved":
        raise ValueError("Pilot discovery must be approved before enrollment.")
    if candidate["status"] != "accepted":
        raise ValueError("Staging candidate must be accepted before enrollment.")
    participant_user_id = (
        str(payload.get("participant_user_id", "")).strip() or None
    )
    if participant_user_id:
        participant = _row(
            conn,
            "SELECT active FROM users WHERE user_id=?",
            (participant_user_id,),
            "Participant user not found.",
        )
        if not participant["active"]:
            raise ValueError("Participant user must be active.")
    support_owner_id = (
        str(payload.get("support_owner_id", "")).strip() or actor_id
    )
    _row(
        conn,
        "SELECT user_id FROM users WHERE user_id=? AND active=1",
        (support_owner_id,),
        "An active support owner is required.",
    )
    cohort_name = str(payload.get("cohort_name", "")).strip()
    scope = str(payload.get("scope", pilot["proposed_scope"])).strip()
    exclusion_scope = str(
        payload.get("exclusion_scope", pilot["exclusion_scope"])
    ).strip()
    if not cohort_name or not scope or not exclusion_scope:
        raise ValueError(
            "Cohort name, controlled scope, and exclusion scope are required."
        )
    now = utc_now()
    enrollment_id = str(
        payload.get("enrollment_id") or _new_id("ENROLL")
    ).strip()
    conn.execute(
        """INSERT INTO pilot_enrollments(
            enrollment_id,pilot_id,candidate_id,contact_id,
            participant_user_id,cohort_name,scope,exclusion_scope,
            support_owner_id,status,activation_reason,activated_by,
            activated_at,created_by,created_at,updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,'onboarding','',NULL,NULL,?,?,?)""",
        (
            enrollment_id,
            pilot_id,
            candidate_id,
            pilot["contact_id"],
            participant_user_id,
            cohort_name,
            scope,
            exclusion_scope,
            support_owner_id,
            actor_id,
            now,
            now,
        ),
    )
    for code, title in REQUIRED_ONBOARDING_CHECKS:
        conn.execute(
            """INSERT INTO pilot_onboarding_checks(
                check_id,enrollment_id,check_code,title,required,status,
                evidence_reference,notes,verified_by,verified_at,created_at
            ) VALUES(?,?,?,?,1,'pending',NULL,'',NULL,NULL,?)""",
            (_new_id("ONBOARD"), enrollment_id, code, title, now),
        )
    _record_status(
        conn,
        enrollment_id,
        "onboarding",
        "Controlled-pilot enrollment created; activation remains blocked.",
        actor_id=actor_id,
        utc_now=utc_now,
    )
    return serialize_enrollment(conn, enrollment_id)


def update_onboarding_check(
    conn: sqlite3.Connection,
    enrollment_id: str,
    payload: dict[str, Any],
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    _enrollment_row(conn, enrollment_id)
    code = str(payload.get("check_code", "")).strip()
    status = str(payload.get("status", "")).strip()
    if status not in {"pending", "completed", "blocked", "not_applicable"}:
        raise ValueError("A valid onboarding-check status is required.")
    check = _row(
        conn,
        """SELECT * FROM pilot_onboarding_checks
           WHERE enrollment_id=? AND check_code=?""",
        (enrollment_id, code),
        "Onboarding check not found.",
    )
    evidence = str(payload.get("evidence_reference", "")).strip() or None
    if status == "completed" and not evidence:
        raise ValueError("Completed onboarding checks require evidence.")
    if check["required"] and status == "not_applicable":
        raise ValueError("Required onboarding checks cannot be marked not applicable.")
    conn.execute(
        """UPDATE pilot_onboarding_checks
           SET status=?,evidence_reference=?,notes=?,
               verified_by=?,verified_at=?
           WHERE check_id=?""",
        (
            status,
            evidence,
            str(payload.get("notes", "")).strip(),
            actor_id if status == "completed" else None,
            utc_now() if status == "completed" else None,
            check["check_id"],
        ),
    )
    return dict(
        _row(
            conn,
            "SELECT * FROM pilot_onboarding_checks WHERE check_id=?",
            (check["check_id"],),
            "Onboarding check not found.",
        )
    )


def record_acknowledgment(
    conn: sqlite3.Connection,
    enrollment_id: str,
    payload: dict[str, Any],
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    _enrollment_row(conn, enrollment_id)
    acknowledgment_type = str(
        payload.get("acknowledgment_type", "")
    ).strip()
    version = str(payload.get("version", "")).strip()
    evidence = str(payload.get("evidence_reference", "")).strip()
    accepted = payload.get("accepted") is True
    if acknowledgment_type not in REQUIRED_ACKNOWLEDGMENTS:
        raise ValueError("A valid acknowledgment type is required.")
    if not version or not evidence or not accepted:
        raise ValueError(
            "Accepted acknowledgment version and evidence are required."
        )
    acknowledgment_id = _new_id("ACK")
    conn.execute(
        """INSERT INTO pilot_acknowledgments(
            acknowledgment_id,enrollment_id,acknowledgment_type,
            version,accepted,evidence_reference,acknowledged_by,
            acknowledged_at
        ) VALUES(?,?,?,?,1,?,?,?)""",
        (
            acknowledgment_id,
            enrollment_id,
            acknowledgment_type,
            version,
            evidence,
            actor_id,
            utc_now(),
        ),
    )
    return dict(
        _row(
            conn,
            """SELECT * FROM pilot_acknowledgments
               WHERE acknowledgment_id=?""",
            (acknowledgment_id,),
            "Pilot acknowledgment not found.",
        )
    )


def activation_blockers(
    conn: sqlite3.Connection,
    enrollment_id: str,
) -> list[str]:
    enrollment = _enrollment_row(conn, enrollment_id)
    blockers: list[str] = []
    candidate = _row(
        conn,
        "SELECT status FROM staging_candidates WHERE candidate_id=?",
        (enrollment["candidate_id"],),
        "Staging candidate not found.",
    )
    pilot = _row(
        conn,
        "SELECT status FROM pilot_discovery_records WHERE pilot_id=?",
        (enrollment["pilot_id"],),
        "Pilot discovery record not found.",
    )
    if candidate["status"] != "accepted":
        blockers.append("The linked staging candidate is not accepted.")
    if pilot["status"] != "approved":
        blockers.append("The linked pilot discovery record is not approved.")
    if not enrollment["participant_user_id"]:
        blockers.append("A participant user must be assigned.")
    missing_checks = [
        row["check_code"]
        for row in conn.execute(
            """SELECT check_code FROM pilot_onboarding_checks
               WHERE enrollment_id=? AND required=1 AND status!='completed'""",
            (enrollment_id,),
        ).fetchall()
    ]
    if missing_checks:
        blockers.append(
            "Required onboarding checks are incomplete: "
            + ", ".join(sorted(missing_checks))
            + "."
        )
    accepted_types = {
        row["acknowledgment_type"]
        for row in conn.execute(
            """SELECT acknowledgment_type FROM pilot_acknowledgments
               WHERE enrollment_id=? AND accepted=1""",
            (enrollment_id,),
        ).fetchall()
    }
    missing_acknowledgments = sorted(
        set(REQUIRED_ACKNOWLEDGMENTS) - accepted_types
    )
    if missing_acknowledgments:
        blockers.append(
            "Required acknowledgments are missing: "
            + ", ".join(missing_acknowledgments)
            + "."
        )
    return blockers


def activate_enrollment(
    conn: sqlite3.Connection,
    enrollment_id: str,
    reason: str,
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    enrollment = _enrollment_row(conn, enrollment_id)
    if enrollment["status"] not in {"onboarding", "paused"}:
        raise ValueError("Only onboarding or paused pilots can be activated.")
    blockers = activation_blockers(conn, enrollment_id)
    if blockers:
        raise ValueError("Pilot activation is blocked: " + " ".join(blockers))
    reason = reason.strip()
    if not reason:
        raise ValueError("A human activation reason is required.")
    now = utc_now()
    _record_status(
        conn,
        enrollment_id,
        "active",
        reason,
        actor_id=actor_id,
        utc_now=utc_now,
    )
    conn.execute(
        """UPDATE pilot_enrollments
           SET activation_reason=?,activated_by=?,activated_at=?,updated_at=?
           WHERE enrollment_id=?""",
        (reason, actor_id, now, now, enrollment_id),
    )
    return serialize_enrollment(conn, enrollment_id)


def create_feedback(
    conn: sqlite3.Connection,
    enrollment_id: str,
    payload: dict[str, Any],
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    enrollment = _enrollment_row(conn, enrollment_id)
    if enrollment["status"] not in {"active", "paused", "completed"}:
        raise ValueError("Feedback requires an activated pilot.")
    category = str(payload.get("category", "")).strip()
    if category not in {
        "usability",
        "workflow",
        "data_quality",
        "research",
        "support",
        "other",
    }:
        raise ValueError("A valid feedback category is required.")
    description = str(payload.get("description", "")).strip()
    if not description:
        raise ValueError("Feedback description is required.")
    rating_value = payload.get("rating")
    rating = None if rating_value in {None, ""} else int(rating_value)
    if rating is not None and not 1 <= rating <= 5:
        raise ValueError("Feedback rating must be between 1 and 5.")
    feedback_id = _new_id("FEEDBACK")
    now = utc_now()
    conn.execute(
        """INSERT INTO pilot_feedback(
            feedback_id,enrollment_id,category,rating,description,
            context,evidence_reference,submitted_by,submitted_at
        ) VALUES(?,?,?,?,?,?,?,?,?)""",
        (
            feedback_id,
            enrollment_id,
            category,
            rating,
            description,
            str(payload.get("context", "")).strip(),
            str(payload.get("evidence_reference", "")).strip() or None,
            actor_id,
            now,
        ),
    )
    conn.execute(
        """INSERT INTO pilot_feedback_reviews(
            review_id,feedback_id,status,disposition,reviewed_by,reviewed_at
        ) VALUES(?,?,'new','',?,?)""",
        (_new_id("FEEDBACKREVIEW"), feedback_id, actor_id, now),
    )
    return dict(
        _row(
            conn,
            "SELECT * FROM pilot_feedback WHERE feedback_id=?",
            (feedback_id,),
            "Pilot feedback not found.",
        )
    )


def review_feedback(
    conn: sqlite3.Connection,
    feedback_id: str,
    payload: dict[str, Any],
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    _row(
        conn,
        "SELECT feedback_id FROM pilot_feedback WHERE feedback_id=?",
        (feedback_id,),
        "Pilot feedback not found.",
    )
    status = str(payload.get("status", "")).strip()
    if status not in {"new", "triaged", "planned", "resolved", "closed"}:
        raise ValueError("A valid feedback-review status is required.")
    review_id = _new_id("FEEDBACKREVIEW")
    conn.execute(
        """INSERT INTO pilot_feedback_reviews(
            review_id,feedback_id,status,disposition,reviewed_by,reviewed_at
        ) VALUES(?,?,?,?,?,?)""",
        (
            review_id,
            feedback_id,
            status,
            str(payload.get("disposition", "")).strip(),
            actor_id,
            utc_now(),
        ),
    )
    return dict(
        _row(
            conn,
            "SELECT * FROM pilot_feedback_reviews WHERE review_id=?",
            (review_id,),
            "Pilot feedback review not found.",
        )
    )


def create_incident(
    conn: sqlite3.Connection,
    enrollment_id: str,
    payload: dict[str, Any],
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    enrollment = _enrollment_row(conn, enrollment_id)
    if enrollment["status"] not in {"active", "paused"}:
        raise ValueError("Incident reporting requires an activated pilot.")
    severity = str(payload.get("severity", "")).strip()
    category = str(payload.get("category", "")).strip()
    if severity not in {"low", "medium", "high", "critical"}:
        raise ValueError("A valid incident severity is required.")
    if category not in {
        "access",
        "privacy",
        "data_integrity",
        "availability",
        "workflow",
        "field_safety",
        "other",
    }:
        raise ValueError("A valid incident category is required.")
    required = {
        key: str(payload.get(key, "")).strip()
        for key in (
            "title",
            "description",
            "impact",
            "immediate_manual_action",
        )
    }
    if not all(required.values()):
        raise ValueError(
            "Incident title, description, impact, and immediate manual action "
            "are required."
        )
    now = utc_now()
    incident_id = _new_id("INCIDENT")
    conn.execute(
        """INSERT INTO pilot_incidents(
            incident_id,enrollment_id,severity,category,title,description,
            impact,immediate_manual_action,evidence_reference,
            reported_by,reported_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        (
            incident_id,
            enrollment_id,
            severity,
            category,
            required["title"],
            required["description"],
            required["impact"],
            required["immediate_manual_action"],
            str(payload.get("evidence_reference", "")).strip() or None,
            actor_id,
            now,
        ),
    )
    conn.execute(
        """INSERT INTO pilot_incident_events(
            event_id,incident_id,status,notes,evidence_reference,
            recorded_by,recorded_at
        ) VALUES(?,?,'open',?,?,?,?)""",
        (
            _new_id("INCIDENTEVENT"),
            incident_id,
            "Incident reported; human triage required.",
            str(payload.get("evidence_reference", "")).strip() or None,
            actor_id,
            now,
        ),
    )
    if severity in SEVERE_INCIDENTS and enrollment["status"] == "active":
        _record_status(
            conn,
            enrollment_id,
            "paused",
            f"Automatic safety pause after {severity} incident {incident_id}; "
            "manual review is required before reactivation.",
            actor_id=actor_id,
            utc_now=utc_now,
        )
    result = dict(
        _row(
            conn,
            "SELECT * FROM pilot_incidents WHERE incident_id=?",
            (incident_id,),
            "Pilot incident not found.",
        )
    )
    result["status"] = "open"
    result["pilot_status"] = _enrollment_row(conn, enrollment_id)["status"]
    return result


def record_incident_event(
    conn: sqlite3.Connection,
    incident_id: str,
    payload: dict[str, Any],
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    incident = _row(
        conn,
        "SELECT * FROM pilot_incidents WHERE incident_id=?",
        (incident_id,),
        "Pilot incident not found.",
    )
    status = str(payload.get("status", "")).strip()
    notes = str(payload.get("notes", "")).strip()
    if status not in {"open", "triaged", "contained", "resolved", "closed"}:
        raise ValueError("A valid incident status is required.")
    if not notes:
        raise ValueError("Incident status notes are required.")
    if status in {"resolved", "closed"} and not str(
        payload.get("evidence_reference", "")
    ).strip():
        raise ValueError("Resolved incidents require evidence.")
    event_id = _new_id("INCIDENTEVENT")
    conn.execute(
        """INSERT INTO pilot_incident_events(
            event_id,incident_id,status,notes,evidence_reference,
            recorded_by,recorded_at
        ) VALUES(?,?,?,?,?,?,?)""",
        (
            event_id,
            incident_id,
            status,
            notes,
            str(payload.get("evidence_reference", "")).strip() or None,
            actor_id,
            utc_now(),
        ),
    )
    result = dict(
        _row(
            conn,
            "SELECT * FROM pilot_incident_events WHERE event_id=?",
            (event_id,),
            "Pilot incident event not found.",
        )
    )
    result["enrollment_id"] = incident["enrollment_id"]
    return result


def record_metric(
    conn: sqlite3.Connection,
    enrollment_id: str,
    payload: dict[str, Any],
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    enrollment = _enrollment_row(conn, enrollment_id)
    if enrollment["status"] not in {"active", "paused", "completed"}:
        raise ValueError("Pilot metrics require an activated pilot.")
    metric_code = str(payload.get("metric_code", "")).strip()
    metric_name = str(payload.get("metric_name", "")).strip()
    unit = str(payload.get("unit", "")).strip()
    direction = str(payload.get("direction", "")).strip()
    evidence_reference = str(payload.get("evidence_reference", "")).strip()
    evidence_sha256 = str(payload.get("evidence_sha256", "")).strip()
    limitations = str(payload.get("limitations", "")).strip()
    if not metric_code or not metric_name or not unit:
        raise ValueError("Metric code, name, and unit are required.")
    if direction not in {"higher", "lower", "range", "informational"}:
        raise ValueError("A valid metric direction is required.")
    if not evidence_reference or len(evidence_sha256) != 64:
        raise ValueError("Metric evidence reference and SHA-256 are required.")
    if not limitations:
        raise ValueError("Metric limitations are required.")
    try:
        observed = float(payload["observed_value"])
        baseline = (
            None
            if payload.get("baseline_value") in {None, ""}
            else float(payload["baseline_value"])
        )
        target = (
            None
            if payload.get("target_value") in {None, ""}
            else float(payload["target_value"])
        )
    except (KeyError, TypeError, ValueError):
        raise ValueError("Pilot metric values must be numeric.") from None
    metric_id = _new_id("METRIC")
    conn.execute(
        """INSERT INTO pilot_metric_observations(
            metric_id,enrollment_id,metric_code,metric_name,baseline_value,
            target_value,observed_value,unit,direction,evidence_reference,
            evidence_sha256,limitations,captured_by,captured_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            metric_id,
            enrollment_id,
            metric_code,
            metric_name,
            baseline,
            target,
            observed,
            unit,
            direction,
            evidence_reference,
            evidence_sha256,
            limitations,
            actor_id,
            utc_now(),
        ),
    )
    return dict(
        _row(
            conn,
            "SELECT * FROM pilot_metric_observations WHERE metric_id=?",
            (metric_id,),
            "Pilot metric not found.",
        )
    )


def release_review_blockers(
    conn: sqlite3.Connection,
    enrollment_id: str,
) -> list[str]:
    enrollment = _enrollment_row(conn, enrollment_id)
    blockers: list[str] = []
    if enrollment["status"] not in {"active", "paused", "completed"}:
        blockers.append("The pilot has not been activated.")
    metric_count = conn.execute(
        """SELECT COUNT(DISTINCT metric_code)
           FROM pilot_metric_observations WHERE enrollment_id=?""",
        (enrollment_id,),
    ).fetchone()[0]
    if metric_count < 3:
        blockers.append("At least three evidence-backed pilot metrics are required.")
    feedback_count = conn.execute(
        "SELECT COUNT(*) FROM pilot_feedback WHERE enrollment_id=?",
        (enrollment_id,),
    ).fetchone()[0]
    if feedback_count < 1:
        blockers.append("At least one immutable participant feedback record is required.")
    post_pilot_count = conn.execute(
        """SELECT COUNT(*) FROM beta_interviews
           WHERE contact_id=? AND interview_type='post_pilot'
             AND completed_at IS NOT NULL""",
        (enrollment["contact_id"],),
    ).fetchone()[0]
    if post_pilot_count < 1:
        blockers.append("A completed post-pilot interview is required.")
    severe_open: list[str] = []
    for incident in conn.execute(
        """SELECT incident_id FROM pilot_incidents
           WHERE enrollment_id=? AND severity IN ('high','critical')""",
        (enrollment_id,),
    ).fetchall():
        if _latest_incident_status(conn, incident["incident_id"]) not in {
            "resolved",
            "closed",
        }:
            severe_open.append(incident["incident_id"])
    if severe_open:
        blockers.append(
            "High or critical incidents remain unresolved: "
            + ", ".join(severe_open)
            + "."
        )
    return blockers


def decide_pilot_exit(
    conn: sqlite3.Connection,
    enrollment_id: str,
    payload: dict[str, Any],
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> dict[str, Any]:
    _enrollment_row(conn, enrollment_id)
    decision = str(payload.get("decision", "")).strip()
    reason = str(payload.get("reason", "")).strip()
    allowed = {
        "continue",
        "extend",
        "pause",
        "complete",
        "stop",
        "recommend_release_review",
    }
    if decision not in allowed or not reason:
        raise ValueError("A valid pilot exit decision and reason are required.")
    blockers = release_review_blockers(conn, enrollment_id)
    if decision == "recommend_release_review" and blockers:
        raise ValueError(
            "Release-review recommendation is blocked: " + " ".join(blockers)
        )
    decision_id = _new_id("PILOTDECISION")
    now = utc_now()
    conn.execute(
        """INSERT INTO pilot_exit_decisions(
            decision_id,enrollment_id,decision,reason,
            blocker_summary_json,decided_by,decided_at
        ) VALUES(?,?,?,?,?,?,?)""",
        (
            decision_id,
            enrollment_id,
            decision,
            reason,
            canonical_json({"blockers": blockers}),
            actor_id,
            now,
        ),
    )
    status_map = {
        "pause": "paused",
        "complete": "completed",
        "stop": "withdrawn",
        "recommend_release_review": "completed",
    }
    if decision in status_map:
        _record_status(
            conn,
            enrollment_id,
            status_map[decision],
            f"Human pilot decision: {decision}. {reason}",
            actor_id=actor_id,
            utc_now=utc_now,
        )
    result = dict(
        _row(
            conn,
            "SELECT * FROM pilot_exit_decisions WHERE decision_id=?",
            (decision_id,),
            "Pilot exit decision not found.",
        )
    )
    result["blocker_summary"] = json.loads(
        result.pop("blocker_summary_json")
    )
    result["production_promoted"] = False
    return result


def pilot_operations_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    enrollments = [
        dict(row)
        for row in conn.execute(
            """SELECT * FROM pilot_enrollments
               ORDER BY updated_at DESC LIMIT 200"""
        ).fetchall()
    ]
    counts = {
        row["status"]: row["n"]
        for row in conn.execute(
            """SELECT status,COUNT(*) AS n FROM pilot_enrollments
               GROUP BY status"""
        ).fetchall()
    }
    incident_counts = {
        row["severity"]: row["n"]
        for row in conn.execute(
            """SELECT severity,COUNT(*) AS n FROM pilot_incidents
               GROUP BY severity"""
        ).fetchall()
    }
    return {
        "schema_version": Q20_Q22_SCHEMA_VERSION,
        "enrollments": enrollments,
        "enrollment_counts": counts,
        "incident_counts": incident_counts,
        "boundaries": [
            "Manual work remains available throughout the pilot.",
            "High or critical incidents pause the pilot for human review.",
            "Release-review recommendations never deploy or promote production.",
            "No automatic equipment control is authorized.",
        ],
    }


def _zip_bytes(files: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(
        output,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, files[name])
    return output.getvalue()


def build_pilot_evidence_export(
    conn: sqlite3.Connection,
    enrollment_id: str,
) -> tuple[bytes, dict[str, Any]]:
    detail = serialize_enrollment(conn, enrollment_id)
    claims = [
        dict(row)
        for row in conn.execute(
            """SELECT * FROM claims_register
               WHERE status IN ('approved','restricted')
               ORDER BY claim_id"""
        ).fetchall()
    ]
    files: dict[str, bytes] = {
        "pilot_enrollment.json": (
            json.dumps(detail, indent=2, ensure_ascii=False, default=str) + "\n"
        ).encode("utf-8"),
        "claims_register.json": (
            json.dumps(claims, indent=2, ensure_ascii=False, default=str) + "\n"
        ).encode("utf-8"),
        "BOUNDARIES.md": (
            "# AgroQ Q20-Q22 evidence boundaries\n\n"
            "- This export records controlled-pilot evidence only.\n"
            "- It does not authorize production promotion or deployment.\n"
            "- It does not authorize automatic equipment control.\n"
            "- Research and agricultural claims remain evidence-gated.\n"
        ).encode("utf-8"),
    }
    file_hashes = {
        name: hashlib.sha256(content).hexdigest()
        for name, content in sorted(files.items())
    }
    manifest = {
        "schema_version": Q20_Q22_SCHEMA_VERSION,
        "enrollment_id": enrollment_id,
        "snapshot_at": detail["updated_at"],
        "files": file_hashes,
        "release_review_blockers": detail["release_review_blockers"],
        "production_promoted": False,
    }
    files["manifest.json"] = (
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    files["SHA256SUMS.txt"] = (
        "".join(
            f"{hashlib.sha256(content).hexdigest()}  {name}\n"
            for name, content in sorted(files.items())
        )
    ).encode("utf-8")
    bundle = _zip_bytes(files)
    return bundle, {
        **manifest,
        "bundle_sha256": hashlib.sha256(bundle).hexdigest(),
    }


def store_pilot_evidence_export(
    conn: sqlite3.Connection,
    enrollment_id: str,
    *,
    actor_id: str,
    utc_now: Callable[[], str],
) -> tuple[bytes, dict[str, Any]]:
    bundle, manifest = build_pilot_evidence_export(conn, enrollment_id)
    export_id = _new_id("PILOTEXPORT")
    filename = f"{enrollment_id.lower()}-q20-q22-evidence.zip"
    conn.execute(
        """INSERT INTO pilot_evidence_exports(
            export_id,enrollment_id,filename,sha256,manifest_json,
            created_by,created_at
        ) VALUES(?,?,?,?,?,?,?)""",
        (
            export_id,
            enrollment_id,
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


def register_pilot_operations(
    *,
    app: Any,
    get_db: Callable[[], Any],
    utc_now: Callable[[], str],
    record_audit_event: Callable[..., None],
    roles_required: Callable[..., Any],
) -> None:
    from flask import Blueprint, Response, g, jsonify, request

    blueprint = Blueprint("pilot_operations", __name__)

    @app.before_request
    def ensure_pilot_operations_tables() -> None:
        with get_db() as conn:
            ensure_pilot_operations_schema(conn)

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

    def participant_allowed(conn: sqlite3.Connection, enrollment_id: str) -> bool:
        enrollment = _enrollment_row(conn, enrollment_id)
        return (
            g.user["role"] in OPERATIONS_ROLES
            or enrollment["participant_user_id"] == g.user["user_id"]
        )

    @blueprint.get("/api/pilots/operations/summary")
    @roles_required(*VIEW_ROLES)
    def operations_summary() -> Response:
        with get_db() as conn:
            return jsonify({"ok": True, **pilot_operations_summary(conn)})

    @blueprint.post("/api/pilots/enrollments")
    @roles_required(*ADMIN_ROLES)
    def api_create_enrollment() -> tuple[Response, int] | Response:
        try:
            with get_db() as conn:
                enrollment = create_enrollment(
                    conn,
                    request.get_json(silent=True) or {},
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except (ValueError, sqlite3.IntegrityError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "pilot_enrollment_created",
            "pilot_enrollment",
            enrollment["enrollment_id"],
            {"status": enrollment["status"]},
        )
        return jsonify({"ok": True, "enrollment": enrollment}), 201

    @blueprint.get("/api/pilots/enrollments/<enrollment_id>")
    @roles_required(*VIEW_ROLES)
    def api_enrollment_detail(
        enrollment_id: str,
    ) -> tuple[Response, int] | Response:
        try:
            with get_db() as conn:
                enrollment = serialize_enrollment(conn, enrollment_id)
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 404
        return jsonify({"ok": True, "enrollment": enrollment})

    @blueprint.post("/api/pilots/enrollments/<enrollment_id>/onboarding")
    @roles_required(*OPERATIONS_ROLES)
    def api_onboarding(
        enrollment_id: str,
    ) -> tuple[Response, int] | Response:
        try:
            with get_db() as conn:
                check = update_onboarding_check(
                    conn,
                    enrollment_id,
                    request.get_json(silent=True) or {},
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "pilot_onboarding_check_recorded",
            "pilot_enrollment",
            enrollment_id,
            {"check_code": check["check_code"], "status": check["status"]},
        )
        return jsonify({"ok": True, "check": check})

    @blueprint.post("/api/pilots/enrollments/<enrollment_id>/acknowledgments")
    @roles_required(*VIEW_ROLES)
    def api_acknowledgment(
        enrollment_id: str,
    ) -> tuple[Response, int] | Response:
        try:
            with get_db() as conn:
                if not participant_allowed(conn, enrollment_id):
                    return jsonify(
                        {"ok": False, "error": "Participant access is required."}
                    ), 403
                acknowledgment = record_acknowledgment(
                    conn,
                    enrollment_id,
                    request.get_json(silent=True) or {},
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except (ValueError, sqlite3.IntegrityError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "pilot_acknowledgment_recorded",
            "pilot_enrollment",
            enrollment_id,
            {"type": acknowledgment["acknowledgment_type"]},
        )
        return jsonify({"ok": True, "acknowledgment": acknowledgment}), 201

    @blueprint.post("/api/pilots/enrollments/<enrollment_id>/activate")
    @roles_required(*ADMIN_ROLES)
    def api_activate(
        enrollment_id: str,
    ) -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True) or {}
        try:
            with get_db() as conn:
                enrollment = activate_enrollment(
                    conn,
                    enrollment_id,
                    str(payload.get("reason", "")),
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 409
        audit(
            "pilot_enrollment_activated",
            "pilot_enrollment",
            enrollment_id,
            {"status": enrollment["status"]},
        )
        return jsonify({"ok": True, "enrollment": enrollment})

    @blueprint.post("/api/pilots/enrollments/<enrollment_id>/feedback")
    @roles_required(*VIEW_ROLES)
    def api_feedback(
        enrollment_id: str,
    ) -> tuple[Response, int] | Response:
        try:
            with get_db() as conn:
                if not participant_allowed(conn, enrollment_id):
                    return jsonify(
                        {"ok": False, "error": "Participant access is required."}
                    ), 403
                feedback = create_feedback(
                    conn,
                    enrollment_id,
                    request.get_json(silent=True) or {},
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except (ValueError, TypeError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "pilot_feedback_submitted",
            "pilot_feedback",
            feedback["feedback_id"],
            {"enrollment_id": enrollment_id},
        )
        return jsonify({"ok": True, "feedback": feedback}), 201

    @blueprint.post("/api/pilots/feedback/<feedback_id>/review")
    @roles_required(*OPERATIONS_ROLES)
    def api_feedback_review(
        feedback_id: str,
    ) -> tuple[Response, int] | Response:
        try:
            with get_db() as conn:
                review = review_feedback(
                    conn,
                    feedback_id,
                    request.get_json(silent=True) or {},
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "pilot_feedback_reviewed",
            "pilot_feedback",
            feedback_id,
            {"status": review["status"]},
        )
        return jsonify({"ok": True, "review": review}), 201

    @blueprint.post("/api/pilots/enrollments/<enrollment_id>/incidents")
    @roles_required(*VIEW_ROLES)
    def api_incident(
        enrollment_id: str,
    ) -> tuple[Response, int] | Response:
        try:
            with get_db() as conn:
                if not participant_allowed(conn, enrollment_id):
                    return jsonify(
                        {"ok": False, "error": "Participant access is required."}
                    ), 403
                incident = create_incident(
                    conn,
                    enrollment_id,
                    request.get_json(silent=True) or {},
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "pilot_incident_reported",
            "pilot_incident",
            incident["incident_id"],
            {
                "severity": incident["severity"],
                "pilot_status": incident["pilot_status"],
            },
        )
        return jsonify({"ok": True, "incident": incident}), 201

    @blueprint.post("/api/pilots/incidents/<incident_id>/events")
    @roles_required(*OPERATIONS_ROLES)
    def api_incident_event(
        incident_id: str,
    ) -> tuple[Response, int] | Response:
        try:
            with get_db() as conn:
                event = record_incident_event(
                    conn,
                    incident_id,
                    request.get_json(silent=True) or {},
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "pilot_incident_status_recorded",
            "pilot_incident",
            incident_id,
            {"status": event["status"]},
        )
        return jsonify({"ok": True, "event": event}), 201

    @blueprint.post("/api/pilots/enrollments/<enrollment_id>/metrics")
    @roles_required(*OPERATIONS_ROLES)
    def api_metric(
        enrollment_id: str,
    ) -> tuple[Response, int] | Response:
        try:
            with get_db() as conn:
                metric = record_metric(
                    conn,
                    enrollment_id,
                    request.get_json(silent=True) or {},
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        audit(
            "pilot_metric_recorded",
            "pilot_metric",
            metric["metric_id"],
            {"metric_code": metric["metric_code"]},
        )
        return jsonify({"ok": True, "metric": metric}), 201

    @blueprint.post("/api/pilots/enrollments/<enrollment_id>/decision")
    @roles_required(*ADMIN_ROLES)
    def api_exit_decision(
        enrollment_id: str,
    ) -> tuple[Response, int] | Response:
        try:
            with get_db() as conn:
                decision = decide_pilot_exit(
                    conn,
                    enrollment_id,
                    request.get_json(silent=True) or {},
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 409
        audit(
            "pilot_exit_decision_recorded",
            "pilot_enrollment",
            enrollment_id,
            {
                "decision": decision["decision"],
                "production_promoted": False,
            },
        )
        return jsonify({"ok": True, "pilot_decision": decision}), 201

    @blueprint.get("/api/pilots/enrollments/<enrollment_id>/evidence.zip")
    @roles_required(*OPERATIONS_ROLES)
    def api_evidence_export(
        enrollment_id: str,
    ) -> tuple[Response, int] | Response:
        try:
            with get_db() as conn:
                bundle, export = store_pilot_evidence_export(
                    conn,
                    enrollment_id,
                    actor_id=g.user["user_id"],
                    utc_now=utc_now,
                )
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 404
        audit(
            "pilot_evidence_exported",
            "pilot_enrollment",
            enrollment_id,
            {"export_id": export["export_id"], "sha256": export["bundle_sha256"]},
        )
        response = Response(bundle, content_type="application/zip")
        response.headers["Content-Disposition"] = (
            f'attachment; filename="{export["filename"]}"'
        )
        response.headers["X-AgroQ-SHA256"] = export["bundle_sha256"]
        response.headers["X-AgroQ-Export-ID"] = export["export_id"]
        return response

    app.register_blueprint(blueprint)
