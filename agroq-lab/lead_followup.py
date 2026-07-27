from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import secrets
import threading
import time
from typing import Any, Callable

from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from notification_center import (
    dispatch_pending_notifications,
    emit_admin_notification,
)


BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / "lead_followup_schema.sql"

LEAD_STATUSES = (
    "new",
    "reviewing",
    "contacted",
    "meeting_scheduled",
    "proposal_sent",
    "waiting_on_customer",
    "onboarded",
    "closed",
    "not_a_fit",
)
LEAD_PRIORITIES = ("low", "normal", "high", "urgent")

_SCHEMA_LOCK = threading.Lock()
_SCHEMA_READY = False


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_follow_up_time(created_at: str | None = None) -> str:
    try:
        base = datetime.fromisoformat((created_at or "").replace("Z", "+00:00"))
    except ValueError:
        base = datetime.now(timezone.utc)
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    return (base + timedelta(days=1)).isoformat(timespec="seconds")


def initialize_lead_followup_schema(get_db: Callable[..., Any]) -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    with _SCHEMA_LOCK:
        if _SCHEMA_READY:
            return
        with get_db() as conn:
            conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        _SCHEMA_READY = True


def ensure_lead_followup(
    get_db: Callable[..., Any],
    *,
    source_type: str,
    source_id: str,
    created_at: str | None = None,
    priority: str = "normal",
) -> None:
    initialize_lead_followup_schema(get_db)
    if source_type not in {"access_request", "beta_reservation", "founding_program"}:
        raise ValueError("Unsupported lead source.")
    if priority not in LEAD_PRIORITIES:
        priority = "normal"
    now = utc_now()
    with get_db() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO lead_followups(
                source_type,source_id,status,priority,next_follow_up_at,
                created_at,updated_at
            ) VALUES(?,?,'new',?,?,?,?)""",
            (
                source_type,
                source_id,
                priority,
                default_follow_up_time(created_at),
                created_at or now,
                now,
            ),
        )


def _table_exists(conn: Any, table_name: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
        is not None
    )


def _lead_rows(get_db: Callable[..., Any]) -> list[dict[str, Any]]:
    initialize_lead_followup_schema(get_db)
    now = utc_now()
    leads: list[dict[str, Any]] = []

    with get_db() as conn:
        access_rows = conn.execute(
            """SELECT request_id AS source_id,'access_request' AS source_type,
                      full_name,email,organization,relationship_type AS interest_type,
                      message AS summary,created_at
               FROM access_requests
               ORDER BY created_at DESC"""
        ).fetchall()
        beta_rows = conn.execute(
            """SELECT reservation_id AS source_id,'beta_reservation' AS source_type,
                      full_name,email,NULL AS organization,'beta_tester' AS interest_type,
                      notes AS summary,created_at
               FROM beta_reservations
               ORDER BY created_at DESC"""
        ).fetchall()

        for row in [*access_rows, *beta_rows]:
            ensure_lead_followup(
                get_db,
                source_type=row["source_type"],
                source_id=row["source_id"],
                created_at=row["created_at"],
            )
            leads.append(dict(row))

        if _table_exists(conn, "founding_program_reservations"):
            founding_rows = conn.execute(
                """SELECT reservation_id AS source_id,
                          'founding_program' AS source_type,
                          full_name,email,organization,
                          'founding_grower' AS interest_type,
                          notes AS summary,created_at
                   FROM founding_program_reservations
                   ORDER BY created_at DESC"""
            ).fetchall()
            for row in founding_rows:
                ensure_lead_followup(
                    get_db,
                    source_type=row["source_type"],
                    source_id=row["source_id"],
                    created_at=row["created_at"],
                    priority="high",
                )
                leads.append(dict(row))

    with get_db() as conn:
        for lead in leads:
            followup = conn.execute(
                """SELECT * FROM lead_followups
                   WHERE source_type=? AND source_id=?""",
                (lead["source_type"], lead["source_id"]),
            ).fetchone()
            lead["followup"] = dict(followup) if followup else {}
            due = lead["followup"].get("next_follow_up_at")
            lead["overdue"] = bool(
                due
                and due < now
                and lead["followup"].get("status")
                not in {"onboarded", "closed", "not_a_fit"}
            )

    leads.sort(key=lambda item: item["created_at"], reverse=True)
    return leads


def register_lead_followup(
    *,
    app: Any,
    get_db: Callable[..., Any],
    roles_required: Callable[..., Any],
    record_audit_event: Callable[..., Any],
) -> None:
    initialize_lead_followup_schema(get_db)
    bp = Blueprint("admin_leads", __name__)

    def csrf_token() -> str:
        token = session.get("lead_followup_csrf")
        if not token:
            token = secrets.token_urlsafe(32)
            session["lead_followup_csrf"] = token
        return token

    def require_csrf() -> None:
        supplied = request.form.get("csrf_token", "")
        expected = session.get("lead_followup_csrf", "")
        if not supplied or not expected or not secrets.compare_digest(supplied, expected):
            abort(400, "Invalid form security token.")

    @bp.get("/admin/leads")
    @roles_required("administrator")
    def lead_page() -> str:
        leads = _lead_rows(get_db)
        counts = {status: 0 for status in LEAD_STATUSES}
        overdue_count = 0
        for lead in leads:
            counts[lead["followup"].get("status", "new")] += 1
            overdue_count += 1 if lead["overdue"] else 0
        return render_template(
            "admin_leads.html",
            leads=leads,
            counts=counts,
            overdue_count=overdue_count,
            statuses=LEAD_STATUSES,
            priorities=LEAD_PRIORITIES,
            csrf_token=csrf_token(),
        )

    @bp.post("/admin/leads/<source_type>/<source_id>/update")
    @roles_required("administrator")
    def update_lead(source_type: str, source_id: str) -> Response:
        require_csrf()
        if source_type not in {"access_request", "beta_reservation", "founding_program"}:
            abort(400, "Unsupported lead source.")

        status = request.form.get("status", "").strip()
        priority = request.form.get("priority", "").strip()
        contact_method = request.form.get("contact_method", "").strip() or None
        next_follow_up_at = request.form.get("next_follow_up_at", "").strip() or None
        note = request.form.get("follow_up_notes", "").strip() or None
        mark_contacted = request.form.get("mark_contacted") == "yes"

        if status not in LEAD_STATUSES:
            abort(400, "Invalid lead status.")
        if priority not in LEAD_PRIORITIES:
            abort(400, "Invalid lead priority.")
        if note and len(note) > 5000:
            abort(400, "Follow-up notes must be 5,000 characters or fewer.")

        initialize_lead_followup_schema(get_db)
        now = utc_now()
        with get_db() as conn:
            current = conn.execute(
                """SELECT * FROM lead_followups
                   WHERE source_type=? AND source_id=?""",
                (source_type, source_id),
            ).fetchone()
            if current is None:
                ensure_lead_followup(
                    get_db,
                    source_type=source_type,
                    source_id=source_id,
                )
                current = conn.execute(
                    """SELECT * FROM lead_followups
                       WHERE source_type=? AND source_id=?""",
                    (source_type, source_id),
                ).fetchone()

            conn.execute(
                """UPDATE lead_followups
                   SET status=?,priority=?,contact_method=?,
                       last_contacted_at=CASE WHEN ? THEN ? ELSE last_contacted_at END,
                       next_follow_up_at=?,follow_up_notes=?,updated_at=?,updated_by=?
                   WHERE source_type=? AND source_id=?""",
                (
                    status,
                    priority,
                    contact_method,
                    1 if mark_contacted else 0,
                    now,
                    next_follow_up_at,
                    note,
                    now,
                    g.user["user_id"],
                    source_type,
                    source_id,
                ),
            )
            conn.execute(
                """INSERT INTO lead_followup_history(
                    history_id,source_type,source_id,previous_status,new_status,
                    priority,contact_method,note,next_follow_up_at,
                    changed_by,changed_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    f"AGQ-LEADHIST-{time.time_ns()}",
                    source_type,
                    source_id,
                    current["status"],
                    status,
                    priority,
                    contact_method,
                    note,
                    next_follow_up_at,
                    g.user["user_id"],
                    now,
                ),
            )

        record_audit_event(
            g.user["user_id"],
            "access_lead_followup_updated",
            source_type,
            source_id,
            json.dumps(
                {
                    "status": status,
                    "priority": priority,
                    "contact_method": contact_method,
                    "next_follow_up_at": next_follow_up_at,
                }
            ),
        )

        event_id = emit_admin_notification(
            get_db,
            event_type="access_activity",
            severity="notice",
            title="AgroQ lead follow-up updated",
            body=f"{source_type} {source_id} moved to {status}.",
            actor_user_id=g.user["user_id"],
            source_entity_type=source_type,
            source_entity_id=source_id,
            metadata={
                "priority": priority,
                "contact_method": contact_method,
                "next_follow_up_at": next_follow_up_at,
                "note": note,
            },
            dedupe_key=f"lead-update:{source_type}:{source_id}:{time.time_ns()}",
        )
        dispatch_pending_notifications(get_db, max_events=20, max_deliveries=50)
        flash(f"Lead status updated. Notification {event_id} recorded.", "info")
        return redirect(url_for("admin_leads.lead_page"))

    app.register_blueprint(bp)
