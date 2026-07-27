from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
import email.message
import json
import os
from pathlib import Path
import re
import secrets
import smtplib
import ssl
import threading
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import (
    Blueprint,
    Response,
    g,
    jsonify,
    render_template,
    request,
    send_from_directory,
    session,
)


BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / "notification_schema.sql"
REDACTED = "[REDACTED]"
SENSITIVE_KEY_RE = re.compile(
    r"(password|passcode|pin|token|secret|cookie|authorization|api[_-]?key)",
    re.IGNORECASE,
)
ALLOWED_EVENT_TYPES = frozenset(
    {
        "login_success",
        "login_failure",
        "access_request",
        "access_activity",
        "invitation_activity",
        "account_activity",
        "password_change",
        "role_change",
        "system_warning",
        "test_notification",
    }
)
ALLOWED_SEVERITIES = frozenset({"info", "notice", "warning", "critical"})
_SCHEMA_LOCK = threading.Lock()



def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"AGQ-{prefix}-{time.time_ns()}"


def sanitize_value(value: Any, *, key: str = "") -> Any:
    if SENSITIVE_KEY_RE.search(key):
        return REDACTED
    if isinstance(value, dict):
        return {
            str(child_key): sanitize_value(child_value, key=str(child_key))
            for child_key, child_value in value.items()
        }
    if isinstance(value, list):
        return [sanitize_value(item) for item in value[:100]]
    if isinstance(value, tuple):
        return [sanitize_value(item) for item in value[:100]]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    text = str(value)
    return text[:2000]


def sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    return sanitize_value(metadata or {})


def audit_action_profile(action: str) -> dict[str, str] | None:
    normalized = action.strip().lower()
    if normalized == "login":
        return {
            "event_type": "login_success",
            "severity": "notice",
            "title": "AgroQ account signed in",
        }
    if "password" in normalized:
        return {
            "event_type": "password_change",
            "severity": "warning",
            "title": "AgroQ password activity",
        }
    if "role" in normalized:
        return {
            "event_type": "role_change",
            "severity": "warning",
            "title": "AgroQ role changed",
        }
    if "access" in normalized:
        return {
            "event_type": "access_activity",
            "severity": "notice",
            "title": "New AgroQ access activity",
        }
    if "invite" in normalized:
        return {
            "event_type": "invitation_activity",
            "severity": "notice",
            "title": "AgroQ invitation activity",
        }
    if any(word in normalized for word in ("account", "profile", "user_created")):
        return {
            "event_type": "account_activity",
            "severity": "notice",
            "title": "AgroQ account activity",
        }
    return None


def _notification_schema_exists(conn: Any) -> bool:
    return conn.execute(
        """SELECT 1 FROM sqlite_master
           WHERE type='table' AND name='admin_notification_events'"""
    ).fetchone() is not None


def initialize_notification_schema(
    get_db: Callable[..., Any],
) -> None:
    with get_db() as conn:
        if _notification_schema_exists(conn):
            return
    with _SCHEMA_LOCK:
        with get_db() as conn:
            if _notification_schema_exists(conn):
                return
            conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
            now = utc_now()
            admins = conn.execute(
                "SELECT user_id FROM users WHERE role='administrator' AND active=1"
            ).fetchall()
            for admin in admins:
                conn.execute(
                    """INSERT OR IGNORE INTO admin_notification_preferences(
                        user_id, created_at, updated_at
                    ) VALUES(?,?,?)""",
                    (admin["user_id"], now, now),
                )
                founder_email = os.environ.get(
                    "AGROQ_NOTIFICATION_EMAIL",
                    "reyesothon1921@gmail.com",
                ).strip()
                if founder_email:
                    conn.execute(
                        """UPDATE admin_notification_preferences
                           SET email_enabled=1,
                               email_address=COALESCE(NULLIF(email_address,''),?),
                               notify_access_changes=1,
                               digest_mode='immediate',
                               updated_at=?
                           WHERE user_id=?""",
                        (founder_email, now, admin["user_id"]),
                    )


def emit_admin_notification(
    get_db: Callable[..., Any],
    *,
    event_type: str,
    severity: str,
    title: str,
    body: str,
    actor_user_id: str | None = None,
    actor_label: str | None = None,
    subject_user_id: str | None = None,
    source_entity_type: str | None = None,
    source_entity_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    dedupe_key: str | None = None,
) -> str:
    initialize_notification_schema(get_db)
    if event_type not in ALLOWED_EVENT_TYPES:
        raise ValueError("Unsupported notification event type.")
    if severity not in ALLOWED_SEVERITIES:
        raise ValueError("Unsupported notification severity.")

    event_id = new_id("NOTIFY")
    safe_metadata = sanitize_metadata(metadata)
    with get_db() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO admin_notification_events(
                event_id, event_type, severity, title, body,
                actor_user_id, actor_label, subject_user_id,
                source_entity_type, source_entity_id, metadata_json,
                dedupe_key, created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                event_id,
                event_type,
                severity,
                title[:180],
                body[:1200],
                actor_user_id,
                (actor_label or "")[:160] or None,
                subject_user_id,
                source_entity_type,
                source_entity_id,
                json.dumps(safe_metadata, separators=(",", ":")),
                dedupe_key,
                utc_now(),
            ),
        )
        stored = conn.execute(
            """SELECT event_id FROM admin_notification_events
               WHERE event_id=? OR dedupe_key=? LIMIT 1""",
            (event_id, dedupe_key),
        ).fetchone()
    return stored["event_id"] if stored else event_id


def _preference_allows(preference: Any, event_type: str) -> bool:
    if event_type == "login_success":
        return bool(preference["notify_login_success"])
    if event_type == "login_failure":
        return bool(preference["notify_login_failure"])
    if event_type == "password_change":
        return bool(preference["notify_password_changes"])
    if event_type in {
        "access_request",
        "access_activity",
        "invitation_activity",
        "account_activity",
        "role_change",
    }:
        return bool(preference["notify_access_changes"])
    return True


def _materialize_deliveries(
    get_db: Callable[..., Any],
    event: Any,
) -> None:
    with get_db() as conn:
        preferences = conn.execute(
            """SELECT p.*, u.display_name
               FROM admin_notification_preferences p
               JOIN users u ON u.user_id=p.user_id
               WHERE u.role='administrator' AND u.active=1"""
        ).fetchall()

        for pref in preferences:
            if not _preference_allows(pref, event["event_type"]):
                continue

            destinations: list[tuple[str, str]] = []
            if pref["email_enabled"] and pref["email_address"]:
                destinations.append(("email", pref["email_address"]))
            if pref["webhook_enabled"] and os.environ.get(
                "AGROQ_ADMIN_WEBHOOK_URL", ""
            ).strip():
                destinations.append(("webhook", "configured-webhook"))
            if pref["web_push_enabled"]:
                subscriptions = conn.execute(
                    """SELECT subscription_id FROM admin_push_subscriptions
                       WHERE user_id=? AND active=1""",
                    (pref["user_id"],),
                ).fetchall()
                destinations.extend(
                    ("web_push", row["subscription_id"])
                    for row in subscriptions
                )

            for channel, destination in destinations:
                conn.execute(
                    """INSERT OR IGNORE INTO admin_notification_deliveries(
                        delivery_id, event_id, channel, destination_label,
                        status, created_at
                    ) VALUES(?,?,?,?,?,?)""",
                    (
                        new_id("DELIVERY"),
                        event["event_id"],
                        channel,
                        destination,
                        "pending",
                        utc_now(),
                    ),
                )


def _send_email(destination: str, event: Any) -> None:
    host = os.environ.get("AGROQ_SMTP_HOST", "").strip()
    username = os.environ.get("AGROQ_SMTP_USERNAME", "").strip()
    password = os.environ.get("AGROQ_SMTP_PASSWORD", "")
    from_address = os.environ.get("AGROQ_SMTP_FROM", "").strip()
    port = int(os.environ.get("AGROQ_SMTP_PORT", "587"))
    use_ssl = os.environ.get("AGROQ_SMTP_SSL", "false").lower() in {
        "1",
        "true",
        "yes",
    }
    if not host or not from_address:
        raise RuntimeError("SMTP is not configured.")

    message = email.message.EmailMessage()
    message["Subject"] = f"[AgroQ] {event['title']}"
    message["From"] = from_address
    message["To"] = destination
    try:
        metadata = json.loads(event.get("metadata_json") or "{}")
    except json.JSONDecodeError:
        metadata = {}
    metadata_lines = []
    for key, value in metadata.items():
        if value in (None, "", [], {}):
            continue
        label = str(key).replace("_", " ").title()
        metadata_lines.append(f"{label}: {value}")
    metadata_text = "\n".join(metadata_lines)
    message.set_content(
        f"{event['body']}\n\n"
        + (f"Submission details:\n{metadata_text}\n\n" if metadata_text else "")
        + f"Severity: {event['severity']}\n"
        + f"Event type: {event['event_type']}\n"
        + f"Created: {event['created_at']}\n"
        + "Open the AgroQ administrator notification center and Lead Follow-up page for details."
    )

    if use_ssl:
        with smtplib.SMTP_SSL(
            host,
            port,
            context=ssl.create_default_context(),
            timeout=20,
        ) as client:
            if username:
                client.login(username, password)
            client.send_message(message)
    else:
        with smtplib.SMTP(host, port, timeout=20) as client:
            client.starttls(context=ssl.create_default_context())
            if username:
                client.login(username, password)
            client.send_message(message)


def _send_webhook(event: Any) -> None:
    url = os.environ.get("AGROQ_ADMIN_WEBHOOK_URL", "").strip()
    if not url.startswith("https://"):
        raise RuntimeError("Webhook must use HTTPS.")
    payload = json.dumps(
        {
            "source": "AgroQ",
            "event_id": event["event_id"],
            "event_type": event["event_type"],
            "severity": event["severity"],
            "title": event["title"],
            "body": event["body"],
            "created_at": event["created_at"],
        }
    ).encode("utf-8")
    req = Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "AgroQ-Notification-Worker/1.0",
        },
    )
    try:
        with urlopen(req, timeout=20) as response:
            if response.status >= 300:
                raise RuntimeError(f"Webhook returned HTTP {response.status}.")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Webhook delivery failed: {exc}") from exc


def _send_web_push(
    get_db: Callable[..., Any],
    subscription_id: str,
    event: Any,
) -> None:
    try:
        from pywebpush import WebPushException, webpush
    except ImportError as exc:
        raise RuntimeError(
            "Web Push dependency is not installed."
        ) from exc

    vapid_private_key = os.environ.get("AGROQ_VAPID_PRIVATE_KEY", "").strip()
    vapid_subject = os.environ.get(
        "AGROQ_VAPID_SUBJECT",
        "mailto:reyesothon1921@gmail.com",
    ).strip()
    if not vapid_private_key:
        raise RuntimeError("VAPID private key is not configured.")

    with get_db() as conn:
        row = conn.execute(
            """SELECT * FROM admin_push_subscriptions
               WHERE subscription_id=? AND active=1""",
            (subscription_id,),
        ).fetchone()
    if row is None:
        raise RuntimeError("Push subscription is inactive or missing.")

    subscription_info = {
        "endpoint": row["endpoint"],
        "keys": {
            "p256dh": row["p256dh"],
            "auth": row["auth_secret"],
        },
    }
    data = json.dumps(
        {
            "title": event["title"],
            "body": event["body"],
            "event_id": event["event_id"],
            "severity": event["severity"],
            "url": "/admin/notifications",
        }
    )
    try:
        webpush(
            subscription_info=subscription_info,
            data=data,
            vapid_private_key=vapid_private_key,
            vapid_claims={"sub": vapid_subject},
            ttl=300,
        )
    except WebPushException as exc:
        raise RuntimeError(f"Web Push failed: {exc}") from exc


def dispatch_pending_notifications(
    get_db: Callable[..., Any],
    *,
    max_events: int = 50,
    max_deliveries: int = 100,
) -> dict[str, int]:
    initialize_notification_schema(get_db)
    with get_db() as conn:
        events = conn.execute(
            """SELECT e.* FROM admin_notification_events e
               WHERE NOT EXISTS(
                   SELECT 1 FROM admin_notification_deliveries d
                   WHERE d.event_id=e.event_id
               )
               ORDER BY e.created_at
               LIMIT ?""",
            (max_events,),
        ).fetchall()

    for event in events:
        _materialize_deliveries(get_db, event)

    with get_db() as conn:
        deliveries = conn.execute(
            """SELECT d.*, e.event_type, e.severity, e.title,
                      e.body, e.metadata_json, e.created_at AS event_created_at
               FROM admin_notification_deliveries d
               JOIN admin_notification_events e ON e.event_id=d.event_id
               WHERE d.status IN ('pending','failed')
                 AND d.attempt_count < 5
               ORDER BY d.created_at
               LIMIT ?""",
            (max_deliveries,),
        ).fetchall()

    result = {"sent": 0, "failed": 0, "skipped": 0}
    for delivery in deliveries:
        event = {
            "event_id": delivery["event_id"],
            "event_type": delivery["event_type"],
            "severity": delivery["severity"],
            "title": delivery["title"],
            "body": delivery["body"],
            "metadata_json": delivery["metadata_json"],
            "created_at": delivery["event_created_at"],
        }
        try:
            if delivery["channel"] == "email":
                _send_email(delivery["destination_label"], event)
            elif delivery["channel"] == "webhook":
                _send_webhook(event)
            elif delivery["channel"] == "web_push":
                _send_web_push(
                    get_db,
                    delivery["destination_label"],
                    event,
                )
            else:
                raise RuntimeError("Unsupported notification channel.")
        except Exception as exc:
            status = "failed"
            error_message = str(exc)[:1000]
            result["failed"] += 1
        else:
            status = "sent"
            error_message = None
            result["sent"] += 1

        with get_db() as conn:
            conn.execute(
                """UPDATE admin_notification_deliveries
                   SET status=?, attempt_count=attempt_count+1,
                       last_attempt_at=?, delivered_at=?,
                       error_message=?
                   WHERE delivery_id=?""",
                (
                    status,
                    utc_now(),
                    utc_now() if status == "sent" else None,
                    error_message,
                    delivery["delivery_id"],
                ),
            )
            if delivery["channel"] == "web_push":
                if status == "sent":
                    conn.execute(
                        """UPDATE admin_push_subscriptions
                           SET last_success_at=?, last_failure_reason=NULL
                           WHERE subscription_id=?""",
                        (utc_now(), delivery["destination_label"]),
                    )
                else:
                    conn.execute(
                        """UPDATE admin_push_subscriptions
                           SET last_failure_at=?, last_failure_reason=?
                           WHERE subscription_id=?""",
                        (
                            utc_now(),
                            error_message,
                            delivery["destination_label"],
                        ),
                    )
    return result


def register_notification_center(
    *,
    app: Any,
    get_db: Callable[..., Any],
    roles_required: Callable[..., Any],
    record_audit_event: Callable[..., Any],
) -> None:
    bp = Blueprint("admin_notifications", __name__)
    def ensure_schema() -> None:
        initialize_notification_schema(get_db)

    def csrf_token() -> str:
        token = session.get("admin_notification_csrf")
        if not token:
            token = secrets.token_urlsafe(32)
            session["admin_notification_csrf"] = token
        return token

    def require_csrf() -> Response | None:
        supplied = request.headers.get("X-CSRF-Token", "")
        expected = session.get("admin_notification_csrf", "")
        if not expected or not secrets.compare_digest(supplied, expected):
            return jsonify({"ok": False, "error": "Invalid CSRF token."}), 403
        return None

    @bp.before_request
    def _initialize() -> None:
        ensure_schema()

    @bp.get("/admin/notifications")
    @roles_required("administrator")
    def notification_page() -> Any:
        return render_template(
            "admin_notifications.html",
            vapid_configured=bool(
                os.environ.get("AGROQ_VAPID_PUBLIC_KEY", "").strip()
            ),
            smtp_configured=bool(
                os.environ.get("AGROQ_SMTP_HOST", "").strip()
                and os.environ.get("AGROQ_SMTP_FROM", "").strip()
            ),
            webhook_configured=bool(
                os.environ.get("AGROQ_ADMIN_WEBHOOK_URL", "").strip()
            ),
        )

    @bp.get("/admin-notification-sw.js")
    def notification_service_worker() -> Response:
        response = send_from_directory(
            BASE_DIR / "static",
            "admin-notification-sw.js",
            mimetype="application/javascript",
        )
        response.headers["Service-Worker-Allowed"] = "/"
        response.headers["Cache-Control"] = "no-cache"
        return response

    @bp.get("/api/admin/notifications")
    @roles_required("administrator")
    def list_notifications() -> Any:
        limit = min(max(int(request.args.get("limit", "50")), 1), 200)
        unread_only = request.args.get("unread", "false").lower() == "true"
        clause = "WHERE acknowledged_at IS NULL" if unread_only else ""
        with get_db() as conn:
            rows = conn.execute(
                f"""SELECT * FROM admin_notification_events
                    {clause}
                    ORDER BY created_at DESC LIMIT ?""",
                (limit,),
            ).fetchall()
            unread = conn.execute(
                """SELECT COUNT(*) AS n FROM admin_notification_events
                   WHERE acknowledged_at IS NULL"""
            ).fetchone()["n"]
            pref = conn.execute(
                """SELECT * FROM admin_notification_preferences
                   WHERE user_id=?""",
                (g.user["user_id"],),
            ).fetchone()
            push_devices = conn.execute(
                """SELECT subscription_id, device_label, user_agent,
                          active, created_at, last_success_at,
                          last_failure_at, last_failure_reason
                   FROM admin_push_subscriptions
                   WHERE user_id=? ORDER BY created_at DESC""",
                (g.user["user_id"],),
            ).fetchall()

        items = []
        for row in rows:
            item = dict(row)
            try:
                item["metadata"] = json.loads(item.pop("metadata_json"))
            except json.JSONDecodeError:
                item["metadata"] = {}
            items.append(item)

        return jsonify(
            {
                "ok": True,
                "notifications": items,
                "unread_count": unread,
                "preferences": dict(pref) if pref else None,
                "push_devices": [dict(row) for row in push_devices],
                "csrf_token": csrf_token(),
                "capabilities": {
                    "in_app": True,
                    "email": bool(
                        os.environ.get("AGROQ_SMTP_HOST", "").strip()
                        and os.environ.get("AGROQ_SMTP_FROM", "").strip()
                    ),
                    "webhook": bool(
                        os.environ.get("AGROQ_ADMIN_WEBHOOK_URL", "").strip()
                    ),
                    "web_push": bool(
                        os.environ.get("AGROQ_VAPID_PUBLIC_KEY", "").strip()
                        and os.environ.get(
                            "AGROQ_VAPID_PRIVATE_KEY",
                            "",
                        ).strip()
                    ),
                    "https_required_for_phone_push": True,
                },
            }
        )

    @bp.get("/api/admin/notifications/summary")
    @roles_required("administrator")
    def notification_summary() -> Any:
        with get_db() as conn:
            unread = conn.execute(
                """SELECT COUNT(*) AS n FROM admin_notification_events
                   WHERE acknowledged_at IS NULL"""
            ).fetchone()["n"]
            critical = conn.execute(
                """SELECT COUNT(*) AS n FROM admin_notification_events
                   WHERE acknowledged_at IS NULL
                     AND severity='critical'"""
            ).fetchone()["n"]
            latest = conn.execute(
                """SELECT event_id, event_type, severity, title, body, created_at
                   FROM admin_notification_events
                   ORDER BY created_at DESC LIMIT 5"""
            ).fetchall()
        return jsonify(
            {
                "ok": True,
                "unread_count": unread,
                "critical_count": critical,
                "latest": [dict(row) for row in latest],
            }
        )

    @bp.post("/api/admin/notifications/<event_id>/acknowledge")
    @roles_required("administrator")
    def acknowledge_notification(event_id: str) -> Any:
        error = require_csrf()
        if error:
            return error
        with get_db() as conn:
            cursor = conn.execute(
                """UPDATE admin_notification_events
                   SET acknowledged_at=?, acknowledged_by=?
                   WHERE event_id=? AND acknowledged_at IS NULL""",
                (utc_now(), g.user["user_id"], event_id),
            )
        if cursor.rowcount == 0:
            return jsonify(
                {"ok": False, "error": "Notification not found or already acknowledged."}
            ), 404
        record_audit_event(
            g.user["user_id"],
            "admin_notification_acknowledged",
            "admin_notification",
            event_id,
        )
        return jsonify({"ok": True})

    @bp.post("/api/admin/notifications/acknowledge-all")
    @roles_required("administrator")
    def acknowledge_all_notifications() -> Any:
        error = require_csrf()
        if error:
            return error
        with get_db() as conn:
            cursor = conn.execute(
                """UPDATE admin_notification_events
                   SET acknowledged_at=?, acknowledged_by=?
                   WHERE acknowledged_at IS NULL""",
                (utc_now(), g.user["user_id"]),
            )
        record_audit_event(
            g.user["user_id"],
            "admin_notifications_acknowledged_all",
            "admin_notification",
            details=json.dumps({"count": cursor.rowcount}),
        )
        return jsonify({"ok": True, "count": cursor.rowcount})

    @bp.post("/api/admin/notification-preferences")
    @roles_required("administrator")
    def update_preferences() -> Any:
        error = require_csrf()
        if error:
            return error
        payload = request.get_json(silent=True) or {}
        boolean_fields = (
            "in_app_enabled",
            "email_enabled",
            "webhook_enabled",
            "web_push_enabled",
            "notify_login_success",
            "notify_login_failure",
            "notify_access_changes",
            "notify_password_changes",
        )
        values = {
            field: 1 if bool(payload.get(field)) else 0
            for field in boolean_fields
        }
        email_address = str(payload.get("email_address", "")).strip()[:320]
        digest_mode = str(payload.get("digest_mode", "immediate")).strip()
        if digest_mode not in {"immediate", "hourly", "daily"}:
            return jsonify({"ok": False, "error": "Invalid digest mode."}), 400

        with get_db() as conn:
            conn.execute(
                """INSERT INTO admin_notification_preferences(
                    user_id, in_app_enabled, email_enabled, email_address,
                    webhook_enabled, web_push_enabled,
                    notify_login_success, notify_login_failure,
                    notify_access_changes, notify_password_changes,
                    digest_mode, created_at, updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(user_id) DO UPDATE SET
                    in_app_enabled=excluded.in_app_enabled,
                    email_enabled=excluded.email_enabled,
                    email_address=excluded.email_address,
                    webhook_enabled=excluded.webhook_enabled,
                    web_push_enabled=excluded.web_push_enabled,
                    notify_login_success=excluded.notify_login_success,
                    notify_login_failure=excluded.notify_login_failure,
                    notify_access_changes=excluded.notify_access_changes,
                    notify_password_changes=excluded.notify_password_changes,
                    digest_mode=excluded.digest_mode,
                    updated_at=excluded.updated_at""",
                (
                    g.user["user_id"],
                    values["in_app_enabled"],
                    values["email_enabled"],
                    email_address or None,
                    values["webhook_enabled"],
                    values["web_push_enabled"],
                    values["notify_login_success"],
                    values["notify_login_failure"],
                    values["notify_access_changes"],
                    values["notify_password_changes"],
                    digest_mode,
                    utc_now(),
                    utc_now(),
                ),
            )
        record_audit_event(
            g.user["user_id"],
            "admin_notification_preferences_updated",
            "admin_notification_preferences",
            g.user["user_id"],
            json.dumps(
                sanitize_metadata(
                    {
                        **values,
                        "email_address": email_address,
                        "digest_mode": digest_mode,
                    }
                )
            ),
        )
        return jsonify({"ok": True})

    @bp.get("/api/admin/push/config")
    @roles_required("administrator")
    def push_config() -> Any:
        public_key = os.environ.get("AGROQ_VAPID_PUBLIC_KEY", "").strip()
        return jsonify(
            {
                "ok": True,
                "configured": bool(public_key),
                "public_key": public_key,
                "https_required": True,
            }
        )

    @bp.post("/api/admin/push/subscribe")
    @roles_required("administrator")
    def push_subscribe() -> Any:
        error = require_csrf()
        if error:
            return error
        payload = request.get_json(silent=True) or {}
        endpoint = str(payload.get("endpoint", "")).strip()
        keys = payload.get("keys") or {}
        p256dh = str(keys.get("p256dh", "")).strip()
        auth_secret = str(keys.get("auth", "")).strip()
        device_label = str(payload.get("device_label", "Administrator device")).strip()
        if not endpoint.startswith("https://") or not p256dh or not auth_secret:
            return jsonify(
                {"ok": False, "error": "Invalid push subscription."}
            ), 400
        subscription_id = new_id("PUSH")
        with get_db() as conn:
            conn.execute(
                """INSERT INTO admin_push_subscriptions(
                    subscription_id, user_id, endpoint, p256dh,
                    auth_secret, user_agent, device_label,
                    active, created_at
                ) VALUES(?,?,?,?,?,?,?,1,?)
                ON CONFLICT(endpoint) DO UPDATE SET
                    user_id=excluded.user_id,
                    p256dh=excluded.p256dh,
                    auth_secret=excluded.auth_secret,
                    user_agent=excluded.user_agent,
                    device_label=excluded.device_label,
                    active=1""",
                (
                    subscription_id,
                    g.user["user_id"],
                    endpoint,
                    p256dh,
                    auth_secret,
                    request.headers.get("User-Agent", "")[:500],
                    device_label[:160],
                    utc_now(),
                ),
            )
        return jsonify({"ok": True})

    @bp.post("/api/admin/push/unsubscribe")
    @roles_required("administrator")
    def push_unsubscribe() -> Any:
        error = require_csrf()
        if error:
            return error
        payload = request.get_json(silent=True) or {}
        endpoint = str(payload.get("endpoint", "")).strip()
        with get_db() as conn:
            conn.execute(
                """UPDATE admin_push_subscriptions
                   SET active=0 WHERE user_id=? AND endpoint=?""",
                (g.user["user_id"], endpoint),
            )
        return jsonify({"ok": True})

    @bp.post("/api/admin/notifications/test")
    @roles_required("administrator")
    def test_notification() -> Any:
        error = require_csrf()
        if error:
            return error
        event_id = emit_admin_notification(
            get_db,
            event_type="test_notification",
            severity="info",
            title="AgroQ notification test",
            body="Your administrator notification center is recording events correctly.",
            actor_user_id=g.user["user_id"],
            subject_user_id=g.user["user_id"],
            source_entity_type="system",
            source_entity_id="notification-center",
            metadata={"requested_from": request.remote_addr},
            dedupe_key=f"notification-test:{g.user['user_id']}:{int(time.time() // 10)}",
        )
        return jsonify({"ok": True, "event_id": event_id})

    app.register_blueprint(bp)
