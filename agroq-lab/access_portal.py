from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
from typing import Any, Callable

from flask import (
    Response,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import generate_password_hash
from lead_followup import ensure_lead_followup


RELATIONSHIP_TYPES = {
    "beta_tester": "Beta tester",
    "investor": "Investor",
    "contributor": "Open-source contributor",
    "partner": "Strategic partner",
    "researcher": "Research collaborator",
    "customer": "Prospective customer",
}
PUBLIC_INVITE_ROLES = {"viewer", "researcher", "field_operator"}
ALL_APP_ROLES = ("administrator", "researcher", "field_operator", "viewer")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,40}$")
BASE_DIR = Path(__file__).resolve().parent


def _new_id(prefix: str) -> str:
    return f"AGQ-{prefix}-{secrets.token_hex(10).upper()}"


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _csrf_token() -> str:
    value = session.get("access_csrf")
    if not value:
        value = secrets.token_urlsafe(32)
        session["access_csrf"] = value
    return value


def _require_csrf() -> None:
    expected = session.get("access_csrf", "")
    supplied = request.form.get("csrf_token", "")
    if not expected or not supplied or not secrets.compare_digest(expected, supplied):
        abort(400, "Invalid form security token.")


def _valid_email(value: str) -> bool:
    return bool(EMAIL_RE.fullmatch(value))


def _active_invitation_policy(
    get_db: Callable[..., Any],
) -> dict[str, Any]:
    fallback = {
        "max_expiry_days": 14,
        "default_max_uses": 1,
        "absolute_max_uses": 5,
        "email_binding_required": False,
        "allowed_roles": ["viewer", "researcher", "field_operator"],
    }
    try:
        with get_db() as conn:
            row = conn.execute(
                "SELECT policy_json FROM invitation_policies "
                "WHERE active=1 ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
    except Exception:
        return fallback
    if row is None:
        return fallback
    try:
        payload = json.loads(row["policy_json"])
    except (TypeError, json.JSONDecodeError):
        return fallback
    return {**fallback, **payload}


def register_access_portal(
    *,
    app: Any,
    get_db: Callable[..., Any],
    utc_now: Callable[[], str],
    record_audit_event: Callable[..., Any],
    roles_required: Callable[..., Any],
) -> None:

    def ensure_schema() -> None:
        sql = (BASE_DIR / "access_schema.sql").read_text(encoding="utf-8")
        with get_db() as conn:
            conn.executescript(sql)

    @app.before_request
    def ensure_access_schema() -> None:
        ensure_schema()

    @app.context_processor
    def access_context() -> dict[str, Any]:
        return {
            "access_relationship_types": RELATIONSHIP_TYPES,
            "access_csrf_token": _csrf_token(),
            "beta_deposit_url": os.environ.get("AGROQ_BETA_DEPOSIT_URL", "").strip(),
        }

    @app.route("/access", methods=["GET", "POST"])
    def access_portal() -> str | Response:
        selected_type = request.values.get("type", "beta_tester")
        if selected_type not in RELATIONSHIP_TYPES:
            selected_type = "beta_tester"
        errors: list[str] = []

        if request.method == "POST":
            _require_csrf()
            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip().lower()
            organization = request.form.get("organization", "").strip() or None
            role_title = request.form.get("role_title", "").strip() or None
            message = request.form.get("message", "").strip() or None
            consent_contact = 1 if request.form.get("consent_contact") == "yes" else 0
            consent_updates = 1 if request.form.get("consent_updates") == "yes" else 0

            if len(full_name) < 2 or len(full_name) > 120:
                errors.append("Enter a name containing 2 to 120 characters.")
            if not _valid_email(email):
                errors.append("Enter a valid email address.")
            if not consent_contact:
                errors.append("Permission to contact you about this request is required.")
            if message and len(message) > 3000:
                errors.append("The message must be 3,000 characters or fewer.")

            if not errors:
                request_id = _new_id("ACCESS")
                with get_db() as conn:
                    conn.execute(
                        '''INSERT INTO access_requests(
                            request_id,relationship_type,full_name,email,organization,
                            role_title,message,consent_contact,consent_updates,
                            status,created_at
                        ) VALUES(?,?,?,?,?,?,?,?,?,'new',?)''',
                        (
                            request_id,
                            selected_type,
                            full_name,
                            email,
                            organization,
                            role_title,
                            message,
                            consent_contact,
                            consent_updates,
                            utc_now(),
                        ),
                    )
                record_audit_event(
                    None,
                    "access_request_created",
                    "access_request",
                    request_id,
                    json.dumps(
                        {
                            "relationship_type": selected_type,
                            "full_name": full_name,
                            "email": email,
                            "organization": organization,
                            "role_title": role_title,
                            "message": message,
                        }
                    ),
                )
                ensure_lead_followup(
                    get_db,
                    source_type="access_request",
                    source_id=request_id,
                    created_at=utc_now(),
                )
                return render_template(
                    "access_request_received.html",
                    request_id=request_id,
                    relationship_label=RELATIONSHIP_TYPES[selected_type],
                )

        return render_template(
            "access_portal.html",
            selected_type=selected_type,
            errors=errors,
            form=request.form,
        )

    @app.route("/access/redeem", methods=["GET", "POST"])
    def redeem_invite() -> str | Response:
        code = request.values.get("code", "").strip()
        invite = None
        errors: list[str] = []

        if request.method == "POST":
            _require_csrf()
            if not code:
                errors.append("Enter an invitation code.")
            else:
                with get_db() as conn:
                    row = conn.execute(
                        "SELECT * FROM invite_codes WHERE code_hash=? AND active=1",
                        (_hash(code),),
                    ).fetchone()
                invite = dict(row) if row else None
                if invite is None:
                    errors.append("The invitation is invalid or inactive.")
                else:
                    if _parse_time(invite["expires_at"]) <= datetime.now(timezone.utc):
                        errors.append("The invitation has expired.")
                    if invite["use_count"] >= invite["max_uses"]:
                        errors.append("The invitation has reached its use limit.")
                    if invite["role"] not in PUBLIC_INVITE_ROLES:
                        errors.append("This invitation cannot be redeemed publicly.")

            if not errors and request.form.get("action") == "create" and invite:
                username = request.form.get("username", "").strip()
                display_name = request.form.get("display_name", "").strip()
                email = request.form.get("email", "").strip().lower()
                password = request.form.get("password", "")
                confirmation = request.form.get("password_confirm", "")
                organization = request.form.get("organization", "").strip() or None
                role_title = request.form.get("role_title", "").strip() or None

                if not USERNAME_RE.fullmatch(username):
                    errors.append("Username must contain 3 to 40 safe characters.")
                if len(display_name) < 2:
                    errors.append("Enter a display name.")
                if not _valid_email(email):
                    errors.append("Enter a valid email address.")
                if invite.get("email") and invite["email"].lower() != email:
                    errors.append("Use the email assigned to this invitation.")
                if len(password) < 12:
                    errors.append("Password must contain at least 12 characters.")
                if password != confirmation:
                    errors.append("Password confirmation does not match.")

                with get_db() as conn:
                    if conn.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone():
                        errors.append("That username is already in use.")
                    if conn.execute("SELECT 1 FROM user_profiles WHERE email=?", (email,)).fetchone():
                        errors.append("That email already has a profile.")

                if not errors:
                    user_id = _new_id("USER")
                    now = utc_now()
                    with get_db() as conn:
                        conn.execute(
                            '''INSERT INTO users(
                                user_id,username,display_name,password_hash,role,
                                site_id,active,created_at
                            ) VALUES(?,?,?,?,?,'AGQ-SITE-001',1,?)''',
                            (
                                user_id,
                                username,
                                display_name,
                                generate_password_hash(password),
                                invite["role"],
                                now,
                            ),
                        )
                        conn.execute(
                            '''INSERT INTO user_profiles(
                                user_id,relationship_type,email,organization,role_title,
                                privacy_level,consent_contact,consent_updates,created_at,updated_at
                            ) VALUES(?,?,?,?,?,'private',0,0,?,?)''',
                            (
                                user_id,
                                invite["relationship_type"],
                                email,
                                organization,
                                role_title,
                                now,
                                now,
                            ),
                        )
                        new_count = invite["use_count"] + 1
                        conn.execute(
                            '''UPDATE invite_codes
                               SET use_count=?,last_used_at=?,
                                   active=CASE WHEN ?>=max_uses THEN 0 ELSE active END
                               WHERE invite_id=?''',
                            (new_count, now, new_count, invite["invite_id"]),
                        )

                    session.clear()
                    session["user_id"] = user_id
                    record_audit_event(
                        user_id,
                        "invite_redeemed",
                        "invite_code",
                        invite["invite_id"],
                    )
                    flash("Your AgroQ profile is ready.", "info")
                    return redirect(url_for("dashboard"))

        return render_template(
            "redeem_invite.html",
            invite=invite,
            code=code,
            errors=errors,
        )

    @app.route("/beta/reserve", methods=["GET", "POST"])
    def beta_reserve() -> str | Response:
        errors: list[str] = []
        if request.method == "POST":
            _require_csrf()
            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip().lower()
            notes = request.form.get("notes", "").strip() or None
            if len(full_name) < 2:
                errors.append("Enter your name.")
            if not _valid_email(email):
                errors.append("Enter a valid email address.")
            if not errors:
                reservation_id = _new_id("RESERVE")
                with get_db() as conn:
                    conn.execute(
                        '''INSERT INTO beta_reservations(
                            reservation_id,email,full_name,status,notes,created_at
                        ) VALUES(?,?,?,'interest_recorded',?,?)''',
                        (reservation_id, email, full_name, notes, utc_now()),
                    )
                record_audit_event(
                    None,
                    "access_beta_reservation_created",
                    "beta_reservation",
                    reservation_id,
                    json.dumps(
                        {
                            "full_name": full_name,
                            "email": email,
                            "notes": notes,
                        }
                    ),
                )
                ensure_lead_followup(
                    get_db,
                    source_type="beta_reservation",
                    source_id=reservation_id,
                    created_at=utc_now(),
                    priority="high",
                )
                return render_template(
                    "beta_reserve.html",
                    submitted=True,
                    reservation_id=reservation_id,
                    errors=[],
                )
        return render_template(
            "beta_reserve.html",
            submitted=False,
            errors=errors,
        )

    @app.route("/profile", methods=["GET", "POST"])
    @roles_required(*ALL_APP_ROLES)
    def account_profile() -> str | Response:
        if request.method == "POST":
            _require_csrf()
            email = request.form.get("email", "").strip().lower()
            relationship = request.form.get("relationship_type", "customer")
            if relationship not in set(RELATIONSHIP_TYPES) | {"founder", "field_staff"}:
                relationship = "customer"
            if not _valid_email(email):
                flash("Enter a valid email address.", "error")
            else:
                now = utc_now()
                with get_db() as conn:
                    conn.execute(
                        '''INSERT INTO user_profiles(
                            user_id,relationship_type,email,organization,role_title,bio,
                            github_url,linkedin_url,privacy_level,consent_contact,
                            consent_updates,created_at,updated_at
                        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                        ON CONFLICT(user_id) DO UPDATE SET
                            relationship_type=excluded.relationship_type,
                            email=excluded.email,
                            organization=excluded.organization,
                            role_title=excluded.role_title,
                            bio=excluded.bio,
                            github_url=excluded.github_url,
                            linkedin_url=excluded.linkedin_url,
                            privacy_level=excluded.privacy_level,
                            consent_contact=excluded.consent_contact,
                            consent_updates=excluded.consent_updates,
                            updated_at=excluded.updated_at''',
                        (
                            g.user["user_id"],
                            relationship,
                            email,
                            request.form.get("organization", "").strip() or None,
                            request.form.get("role_title", "").strip() or None,
                            request.form.get("bio", "").strip() or None,
                            request.form.get("github_url", "").strip() or None,
                            request.form.get("linkedin_url", "").strip() or None,
                            request.form.get("privacy_level", "private"),
                            1 if request.form.get("consent_contact") == "yes" else 0,
                            1 if request.form.get("consent_updates") == "yes" else 0,
                            now,
                            now,
                        ),
                    )
                record_audit_event(
                    g.user["user_id"],
                    "profile_updated",
                    "user_profile",
                    g.user["user_id"],
                )
                flash("Profile updated.", "info")
                return redirect(url_for("account_profile"))

        with get_db() as conn:
            profile = conn.execute(
                "SELECT * FROM user_profiles WHERE user_id=?",
                (g.user["user_id"],),
            ).fetchone()
        return render_template("profile.html", profile=profile)

    @app.route("/admin/access", methods=["GET", "POST"])
    @roles_required("administrator")
    def admin_access() -> str | Response:
        generated_code = None
        if request.method == "POST":
            _require_csrf()
            relationship = request.form.get("relationship_type", "beta_tester")
            role = request.form.get("role", "viewer")
            email = request.form.get("email", "").strip().lower() or None
            policy = _active_invitation_policy(get_db)
            max_days = max(1, min(90, int(policy.get("max_expiry_days", 14))))
            absolute_max_uses = max(
                1,
                min(25, int(policy.get("absolute_max_uses", 5))),
            )
            default_max_uses = max(
                1,
                min(
                    absolute_max_uses,
                    int(policy.get("default_max_uses", 1)),
                ),
            )
            days = max(
                1,
                min(
                    max_days,
                    int(request.form.get("expires_days", str(max_days))),
                ),
            )
            max_uses = max(
                1,
                min(
                    absolute_max_uses,
                    int(
                        request.form.get(
                            "max_uses",
                            str(default_max_uses),
                        )
                    ),
                ),
            )
            allowed_roles = set(
                policy.get(
                    "allowed_roles",
                    ["viewer", "researcher", "field_operator"],
                )
            )
            if relationship not in RELATIONSHIP_TYPES:
                abort(400, "Invalid relationship type.")
            if role not in PUBLIC_INVITE_ROLES or role not in allowed_roles:
                abort(400, "Invalid role.")
            if policy.get("email_binding_required") and not email:
                abort(400, "This invitation policy requires an email.")
            if email and not _valid_email(email):
                abort(400, "Invalid email.")
            generated_code = secrets.token_urlsafe(24)
            invite_id = _new_id("INVITE")
            expires_at = (
                datetime.now(timezone.utc) + timedelta(days=days)
            ).isoformat(timespec="seconds")
            with get_db() as conn:
                conn.execute(
                    '''INSERT INTO invite_codes(
                        invite_id,code_hash,code_hint,relationship_type,role,email,
                        expires_at,max_uses,use_count,active,note,created_by,created_at
                    ) VALUES(?,?,?,?,?,?,?,?,0,1,?,?,?)''',
                    (
                        invite_id,
                        _hash(generated_code),
                        generated_code[-6:],
                        relationship,
                        role,
                        email,
                        expires_at,
                        max_uses,
                        request.form.get("note", "").strip() or None,
                        g.user["user_id"],
                        utc_now(),
                    ),
                )
            record_audit_event(
                g.user["user_id"],
                "invite_created",
                "invite_code",
                invite_id,
            )

        with get_db() as conn:
            access_requests = conn.execute(
                "SELECT * FROM access_requests ORDER BY created_at DESC LIMIT 100"
            ).fetchall()
            invites = conn.execute(
                "SELECT * FROM invite_codes ORDER BY created_at DESC LIMIT 100"
            ).fetchall()
            reservations = conn.execute(
                "SELECT * FROM beta_reservations ORDER BY created_at DESC LIMIT 100"
            ).fetchall()
        return render_template(
            "admin_access.html",
            requests=access_requests,
            invites=invites,
            reservations=reservations,
            generated_code=generated_code,
        )

    @app.route("/access/admin-link", methods=["GET", "POST"])
    def temporary_admin_link() -> str | Response:
        token = request.values.get("token", "").strip()
        token_row = None
        error = None
        if token:
            with get_db() as conn:
                row = conn.execute(
                    '''SELECT t.*,u.username,u.display_name,u.role,u.active
                       FROM temporary_login_tokens t
                       JOIN users u ON u.user_id=t.user_id
                       WHERE t.token_hash=?''',
                    (_hash(token),),
                ).fetchone()
            token_row = dict(row) if row else None

        if token_row is None:
            error = "The temporary sign-in link is invalid."
        elif token_row["used_at"]:
            error = "The temporary sign-in link has already been used."
        elif _parse_time(token_row["expires_at"]) <= datetime.now(timezone.utc):
            error = "The temporary sign-in link has expired."
        elif token_row["role"] != "administrator" or not token_row["active"]:
            error = "The temporary sign-in link is not authorized."

        if request.method == "POST":
            _require_csrf()
            if error:
                return render_template(
                    "admin_magic_link.html",
                    error=error,
                    token=token,
                    token_row=token_row,
                ), 400
            with get_db() as conn:
                conn.execute(
                    "UPDATE temporary_login_tokens SET used_at=? WHERE token_id=? AND used_at IS NULL",
                    (utc_now(), token_row["token_id"]),
                )
            session.clear()
            session["user_id"] = token_row["user_id"]
            record_audit_event(
                token_row["user_id"],
                "temporary_admin_link_used",
                "temporary_login_token",
                token_row["token_id"],
            )
            return redirect(url_for("dashboard"))

        return render_template(
            "admin_magic_link.html",
            error=error,
            token=token,
            token_row=token_row,
        )

    @app.get("/api/access/session")
    def api_access_session() -> Response:
        if g.user is None:
            return jsonify(
                {
                    "authenticated": False,
                    "login_url": url_for("login"),
                    "access_url": url_for("access_portal"),
                    "redeem_url": url_for("redeem_invite"),
                }
            )
        return jsonify(
            {
                "authenticated": True,
                "user": {
                    "username": g.user["username"],
                    "display_name": g.user["display_name"],
                    "role": g.user["role"],
                },
                "profile_url": url_for("account_profile"),
            }
        )
