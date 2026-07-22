from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Iterator
import csv
import io
import json
import os
import sqlite3
import time
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from flask import (
    Flask,
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
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("AGROQ_DB_PATH", BASE_DIR / "instance" / "agroq.db"))

# Development-only fallback — change AGROQ_SECRET_KEY before deployment.
DEV_SECRET_KEY = "agroq-dev-secret-key-change-before-deployment"
# Development-only admin defaults — set AGROQ_ADMIN_USERNAME and AGROQ_ADMIN_PASSWORD locally.
DEV_ADMIN_USERNAME = "admin"
DEV_ADMIN_PASSWORD = "agroq-dev-change-me"

VALID_ROLES = frozenset({"administrator", "researcher", "field_operator", "viewer"})
PLOT_STATUSES = frozenset({"Active", "Retired"})
PLOT_TYPES = frozenset({"control", "treatment", "calibration", "observation", "other"})
ASSET_STATUSES = frozenset({"online", "available", "testing", "offline", "retired", "maintenance"})
REGISTRY_VIEW_ROLES = ("administrator", "researcher", "field_operator", "viewer")
REGISTRY_EDIT_ROLES = ("administrator", "researcher")
REGISTRY_RETIRE_ROLES = ("administrator",)
ASSET_OPERATIONAL_ROLES = ("administrator", "researcher", "field_operator")
OBSERVATION_SOURCE_TYPES = frozenset({"manual", "sensor", "laboratory", "import"})
OBSERVATION_QUALITY_FLAGS = frozenset({"unverified", "good", "suspect", "invalid"})
CORRECTION_QUALITY_FLAGS = frozenset({"corrected", "good", "suspect", "invalid"})
OBSERVATION_VIEW_ROLES = ("administrator", "researcher", "field_operator", "viewer")
OBSERVATION_CREATE_ROLES = ("administrator", "researcher", "field_operator")
EXPERIMENT_STATUSES = frozenset({"draft", "planned", "active", "paused", "completed", "cancelled"})
EXPERIMENT_VIEW_ROLES = REGISTRY_VIEW_ROLES
EXPERIMENT_EDIT_ROLES = ("administrator", "researcher")
TASK_VIEW_ROLES = REGISTRY_VIEW_ROLES
TASK_CREATE_ROLES = ("administrator", "researcher", "field_operator")
TASK_WORK_ROLES = ("administrator", "field_operator")
TASK_APPROVAL_ROLES = ("administrator", "researcher")
TASK_TYPES = frozenset({"fieldwork", "inspection", "sampling", "calibration", "maintenance", "repair", "treatment"})
TASK_PRIORITIES = frozenset({"normal", "high", "critical"})
TASK_STATUSES = frozenset({"open", "in_progress", "completed", "cancelled"})

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
app.secret_key = os.environ.get("AGROQ_SECRET_KEY", DEV_SECRET_KEY)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_audit_id() -> str:
    return f"AGQ-AUDIT-{time.time_ns()}"


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        with conn:
            yield conn
    finally:
        conn.close()


def record_audit_event(
    user_id: str | None,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    details: str | None = None,
) -> None:
    with get_db() as conn:
        conn.execute(
            """INSERT INTO audit_events(
                audit_id, user_id, action, entity_type, entity_id, details, created_at
            ) VALUES(?,?,?,?,?,?,?)""",
            (new_audit_id(), user_id, action, entity_type, entity_id, details, utc_now()),
        )


def new_plot_id() -> str:
    return f"AGQ-PLOT-{int(datetime.now().timestamp() * 1000)}"


def new_asset_id() -> str:
    return f"AGQ-ASSET-{int(datetime.now().timestamp() * 1000)}"


def new_observation_id() -> str:
    return f"AGQ-OBS-{int(datetime.now().timestamp() * 1000)}"


def new_correction_id() -> str:
    return f"AGQ-CORR-{int(datetime.now().timestamp() * 1000)}"


def new_entity_id(prefix: str) -> str:
    return f"AGQ-{prefix}-{time.time_ns()}"


def validate_experiment_payload(conn: sqlite3.Connection, payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not str(payload.get("title", "")).strip():
        errors.append("Title is required.")
    if not str(payload.get("hypothesis", "")).strip():
        errors.append("Hypothesis is required.")
    status = str(payload.get("status", "draft")).strip()
    if status not in EXPERIMENT_STATUSES:
        errors.append("Experiment status is invalid.")
    plot_id = str(payload.get("plot_id", "")).strip()
    if plot_id and not plot_exists(conn, plot_id):
        errors.append("Selected primary plot does not exist.")
    return errors


def next_revision(current: str) -> str:
    if current.startswith("rev-") and len(current) == 5 and current[4].isalpha():
        letter = current[4]
        if letter == "z":
            return "rev-aa"
        return f"rev-{chr(ord(letter) + 1)}"
    return "rev-b"


def get_plot(conn: sqlite3.Connection, plot_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM plots WHERE plot_id = ?", (plot_id,)).fetchone()


def get_asset(conn: sqlite3.Connection, asset_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM assets WHERE asset_id = ?", (asset_id,)).fetchone()


def plot_exists(conn: sqlite3.Connection, plot_id: str | None) -> bool:
    if not plot_id:
        return True
    return get_plot(conn, plot_id) is not None


def validate_plot_payload(payload: dict[str, Any], *, require_status: bool = True) -> list[str]:
    errors: list[str] = []
    if not payload.get("name", "").strip():
        errors.append("Name is required.")
    plot_type = payload.get("plot_type", "").strip()
    if not plot_type:
        errors.append("Plot type is required.")
    elif plot_type not in PLOT_TYPES:
        errors.append(f"Plot type must be one of: {', '.join(sorted(PLOT_TYPES))}.")
    status = payload.get("status", "").strip()
    if require_status:
        if not status:
            errors.append("Status is required.")
        elif status not in PLOT_STATUSES:
            errors.append(f"Status must be one of: {', '.join(sorted(PLOT_STATUSES))}.")
    elif status and status not in PLOT_STATUSES:
        errors.append(f"Status must be one of: {', '.join(sorted(PLOT_STATUSES))}.")
    return errors


def validate_asset_payload(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    require_status: bool = True,
) -> list[str]:
    errors: list[str] = []
    if not payload.get("name", "").strip():
        errors.append("Name is required.")
    if not payload.get("asset_type", "").strip():
        errors.append("Asset type is required.")
    plot_id = payload.get("plot_id") or None
    if plot_id and not plot_exists(conn, plot_id):
        errors.append("Assigned plot does not exist.")
    status = payload.get("status", "").strip()
    if require_status:
        if not status:
            errors.append("Status is required.")
        elif status not in ASSET_STATUSES:
            errors.append(f"Status must be one of: {', '.join(sorted(ASSET_STATUSES))}.")
    elif status and status not in ASSET_STATUSES:
        errors.append(f"Status must be one of: {', '.join(sorted(ASSET_STATUSES))}.")
    return errors


def validate_observation_payload(conn: sqlite3.Connection, payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    plot_id = str(payload.get("plot_id", "")).strip()
    if not plot_id:
        errors.append("Plot is required.")
    elif not plot_exists(conn, plot_id):
        errors.append("Selected plot does not exist.")
    asset_id = str(payload.get("asset_id", "")).strip()
    if asset_id:
        asset = get_asset(conn, asset_id)
        if asset is None:
            errors.append("Selected asset does not exist.")
        elif asset["plot_id"] and asset["plot_id"] != plot_id:
            errors.append("Selected asset is assigned to a different plot.")
    if not str(payload.get("observed_property", "")).strip():
        errors.append("Observed property is required.")
    try:
        float(payload.get("value", ""))
    except (TypeError, ValueError):
        errors.append("Value must be numeric.")
    if not str(payload.get("unit", "")).strip():
        errors.append("Unit is required.")
    source_type = str(payload.get("source_type", "")).strip()
    if source_type not in OBSERVATION_SOURCE_TYPES:
        errors.append("Source type is invalid.")
    quality_flag = str(payload.get("quality_flag", "unverified")).strip()
    if quality_flag not in OBSERVATION_QUALITY_FLAGS:
        errors.append("Quality flag is invalid.")
    return errors


def plot_retire_blockers(conn: sqlite3.Connection, plot_id: str) -> list[str]:
    blockers: list[str] = []
    active_assets = conn.execute(
        """SELECT COUNT(*) AS n FROM assets
           WHERE plot_id = ? AND status NOT IN ('retired', 'offline')""",
        (plot_id,),
    ).fetchone()["n"]
    if active_assets:
        blockers.append(f"{active_assets} active asset(s) still assigned to this plot")
    active_experiments = conn.execute(
        "SELECT COUNT(*) AS n FROM experiments WHERE plot_id = ? AND status = 'active'",
        (plot_id,),
    ).fetchone()["n"]
    if active_experiments:
        blockers.append(f"{active_experiments} active experiment(s) linked to this plot")
    open_tasks = conn.execute(
        "SELECT COUNT(*) AS n FROM manual_tasks WHERE plot_id = ? AND status != 'completed'",
        (plot_id,),
    ).fetchone()["n"]
    if open_tasks:
        blockers.append(f"{open_tasks} open manual task(s) linked to this plot")
    return blockers


def seed_auth(conn: sqlite3.Connection) -> None:
    now = utc_now()
    site_count = conn.execute("SELECT COUNT(*) AS n FROM sites").fetchone()["n"]
    if site_count == 0:
        conn.execute(
            """INSERT INTO sites(site_id, name, location, status, owner, created_at)
               VALUES(?,?,?,?,?,?)""",
            (
                "AGQ-SITE-001",
                "AgroQ One-Acre Living Laboratory",
                None,
                "active",
                None,
                now,
            ),
        )

    user_count = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
    if user_count == 0:
        username = os.environ.get("AGROQ_ADMIN_USERNAME", DEV_ADMIN_USERNAME)
        password = os.environ.get("AGROQ_ADMIN_PASSWORD", DEV_ADMIN_PASSWORD)
        password_hash = generate_password_hash(password)
        conn.execute(
            """INSERT INTO users(
                user_id, username, display_name, password_hash, role, site_id, active, created_at
            ) VALUES(?,?,?,?,?,?,?,?)""",
            (
                "AGQ-USER-001",
                username,
                "AgroQ Administrator",
                password_hash,
                "administrator",
                "AGQ-SITE-001",
                1,
                now,
            ),
        )


def init_db() -> None:
    schema = (BASE_DIR / "schema.sql").read_text(encoding="utf-8")
    with get_db() as conn:
        conn.executescript(schema)
        seed_auth(conn)
        count = conn.execute("SELECT COUNT(*) AS n FROM plots").fetchone()["n"]
        if count == 0:
            seed_db(conn)


def seed_db(conn: sqlite3.Connection) -> None:
    now = utc_now()
    plots = [
        ("AGQ-PLOT-001", "North Control", "control", "0.10 acre", "Active"),
        ("AGQ-PLOT-002", "Compost Treatment", "treatment", "0.10 acre", "Active"),
        ("AGQ-PLOT-003", "Beneficial Organism Zone", "treatment", "0.10 acre", "Active"),
        ("AGQ-PLOT-004", "Sensor Calibration Zone", "calibration", "0.05 acre", "Active"),
    ]
    conn.executemany(
        "INSERT INTO plots(plot_id, name, plot_type, area, status, created_at) VALUES(?,?,?,?,?,?)",
        [p + (now,) for p in plots],
    )

    assets = [
        ("AGQ-ASSET-001", "Edge Gateway", "gateway", "AGQ-PLOT-004", "online", "rev-a", now),
        ("AGQ-ASSET-002", "Manual Soil Probe", "manual-tool", "AGQ-PLOT-001", "available", "rev-a", now),
        ("AGQ-ASSET-003", "Prototype Sensor Node", "sensor-node", "AGQ-PLOT-002", "testing", "rev-a", now),
    ]
    conn.executemany(
        """INSERT INTO assets(asset_id, name, asset_type, plot_id, status, revision, created_at)
           VALUES(?,?,?,?,?,?,?)""",
        assets,
    )

    experiments = [
        (
            "AGQ-EXP-001",
            "Manual vs sensor soil-moisture comparison",
            "Compare manual probe readings with prototype node readings.",
            "active",
            "AGQ-PLOT-002",
            "Othon Reyes Jr.",
            now,
        )
    ]
    conn.executemany(
        """INSERT INTO experiments(experiment_id, title, hypothesis, status, plot_id, owner, created_at)
           VALUES(?,?,?,?,?,?,?)""",
        experiments,
    )

    observations = [
        (
            "AGQ-OBS-001",
            "AGQ-PLOT-001",
            None,
            "soil_moisture",
            24.0,
            "%",
            "manual",
            "good",
            "Baseline manual reading",
            now,
            now,
        ),
        (
            "AGQ-OBS-002",
            "AGQ-PLOT-002",
            "AGQ-ASSET-003",
            "soil_moisture",
            27.5,
            "%",
            "sensor",
            "unverified",
            "Prototype reading awaiting manual comparison",
            now,
            now,
        ),
    ]
    conn.executemany(
        """INSERT INTO observations(
            observation_id, plot_id, asset_id, observed_property, value, unit,
            source_type, quality_flag, notes, observed_at, created_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        observations,
    )

    tasks = [
        (
            "AGQ-TASK-001",
            "Inspect prototype enclosure seal",
            "maintenance",
            "AGQ-PLOT-002",
            "open",
            "high",
            "Field team",
            "Check moisture, gasket seating, and cable gland.",
            now,
        )
    ]
    conn.executemany(
        """INSERT INTO manual_tasks(
            task_id, title, task_type, plot_id, status, priority, assigned_to, notes, created_at
        ) VALUES(?,?,?,?,?,?,?,?,?)""",
        tasks,
    )

    recommendations = [
        (
            "AGQ-REC-001",
            "Inspect soil moisture before irrigation",
            "Do not irrigate automatically. Take one manual reading in the treatment plot and compare it with the sensor.",
            "rule",
            "baseline-rule-v1",
            "Medium",
            "pending",
            "AGQ-PLOT-002",
            now,
        )
    ]
    conn.executemany(
        """INSERT INTO recommendations(
            recommendation_id, title, rationale, source_type, source_version,
            confidence, approval_status, plot_id, created_at
        ) VALUES(?,?,?,?,?,?,?,?,?)""",
        recommendations,
    )


def is_api_request() -> bool:
    return request.path.startswith("/api/")


def login_required(view: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        if g.user is None:
            if is_api_request():
                return jsonify({"ok": False, "error": "Authentication required"}), 401
            return redirect(url_for("login", next=request.url))
        return view(*args, **kwargs)

    return wrapped


def roles_required(*roles: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    allowed = frozenset(roles)

    def decorator(view: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(view)
        @login_required
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            if g.user["role"] not in allowed:
                if is_api_request():
                    return jsonify({"ok": False, "error": "Insufficient permissions"}), 403
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


@app.before_request
def ensure_database() -> None:
    init_db()


@app.before_request
def load_user() -> None:
    g.user = None
    user_id = session.get("user_id")
    if not user_id:
        return
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE user_id = ? AND active = 1",
            (user_id,),
        ).fetchone()
    if row is None:
        session.pop("user_id", None)
        return
    g.user = dict(row)


@app.route("/login", methods=["GET", "POST"])
def login() -> str | Response:
    if g.user is not None:
        return redirect(url_for("dashboard"))

    error: str | None = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ? AND active = 1",
                (username,),
            ).fetchone()
        if user is not None and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["user_id"]
            record_audit_event(user["user_id"], "login", "user", user["user_id"])
            next_url = request.args.get("next") or url_for("dashboard")
            return redirect(next_url)
        error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.post("/logout")
def logout() -> Response:
    user_id = session.get("user_id")
    if user_id:
        record_audit_event(user_id, "logout", "user", user_id)
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("login"))


@app.get("/")
@roles_required("administrator", "researcher", "field_operator", "viewer")
def dashboard() -> str:
    with get_db() as conn:
        counts = {
            "plots": conn.execute("SELECT COUNT(*) AS n FROM plots").fetchone()["n"],
            "assets": conn.execute("SELECT COUNT(*) AS n FROM assets").fetchone()["n"],
            "observations": conn.execute("SELECT COUNT(*) AS n FROM observations").fetchone()["n"],
            "open_tasks": conn.execute(
                "SELECT COUNT(*) AS n FROM manual_tasks WHERE status != 'completed'"
            ).fetchone()["n"],
            "pending_recommendations": conn.execute(
                "SELECT COUNT(*) AS n FROM recommendations WHERE approval_status = 'pending'"
            ).fetchone()["n"],
        }
        recent = conn.execute(
            """SELECT o.*, p.name AS plot_name
               FROM observations o JOIN plots p ON p.plot_id = o.plot_id
               ORDER BY o.observed_at DESC LIMIT 8"""
        ).fetchall()
        tasks = conn.execute(
            "SELECT * FROM manual_tasks ORDER BY created_at DESC LIMIT 8"
        ).fetchall()
        recommendations = conn.execute(
            "SELECT * FROM recommendations ORDER BY created_at DESC LIMIT 8"
        ).fetchall()
    return render_template(
        "dashboard.html",
        counts=counts,
        recent=recent,
        tasks=tasks,
        recommendations=recommendations,
    )


@app.route("/observations/new", methods=["GET", "POST"])
@roles_required(*OBSERVATION_CREATE_ROLES)
def new_observation() -> str | Response:
    if request.method == "POST":
        payload = request.form.to_dict()
        try:
            observation_id = create_observation(payload, g.user["user_id"])
        except ValueError as exc:
            flash(str(exc), "error")
        else:
            flash("Observation recorded. The raw record is now immutable.", "info")
            return redirect(url_for("observation_detail", observation_id=observation_id))
    with get_db() as conn:
        plots = conn.execute("SELECT * FROM plots ORDER BY plot_id").fetchall()
        assets = conn.execute("SELECT * FROM assets ORDER BY asset_id").fetchall()
    return render_template("observation_form.html", plots=plots, assets=assets)


def create_observation(payload: dict[str, Any], user_id: str | None = None) -> str:
    with get_db() as conn:
        errors = validate_observation_payload(conn, payload)
    if errors:
        raise ValueError(" ".join(errors))
    observation_id = str(payload.get("observation_id") or new_observation_id()).strip()
    observed_at = payload.get("observed_at") or utc_now()
    try:
        with get_db() as conn:
            conn.execute(
                """INSERT INTO observations(
                    observation_id, plot_id, asset_id, observed_property, value, unit,
                    source_type, quality_flag, notes, observed_at, created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    observation_id, str(payload["plot_id"]).strip(),
                    str(payload.get("asset_id", "")).strip() or None,
                    str(payload["observed_property"]).strip(), float(payload["value"]),
                    str(payload["unit"]).strip(), str(payload["source_type"]).strip(),
                    str(payload.get("quality_flag", "unverified")).strip(),
                    str(payload.get("notes", "")).strip(), observed_at, utc_now(),
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError("Observation ID already exists or a linked record is invalid.") from exc
    record_audit_event(user_id, "observation_created", "observation", observation_id,
                       json.dumps({"source_type": payload["source_type"], "plot_id": payload["plot_id"]}))
    return observation_id


@app.post("/api/observations")
@roles_required(*OBSERVATION_CREATE_ROLES)
def api_create_observation() -> tuple[Response, int] | Response:
    payload = request.get_json(silent=True) or {}
    try:
        observation_id = create_observation(payload, g.user["user_id"])
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": True, "observation_id": observation_id}), 201


@app.get("/observations")
@roles_required(*OBSERVATION_VIEW_ROLES)
def observations() -> str:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT o.*, p.name AS plot_name,
                      (SELECT COUNT(*) FROM observation_corrections c
                       WHERE c.observation_id = o.observation_id) AS correction_count
               FROM observations o JOIN plots p ON p.plot_id = o.plot_id
               ORDER BY o.observed_at DESC"""
        ).fetchall()
    return render_template("observations.html", observations=rows)


@app.get("/observations/<observation_id>")
@roles_required(*OBSERVATION_VIEW_ROLES)
def observation_detail(observation_id: str) -> str:
    with get_db() as conn:
        observation = conn.execute(
            """SELECT o.*, p.name AS plot_name, a.name AS asset_name
               FROM observations o JOIN plots p ON p.plot_id = o.plot_id
               LEFT JOIN assets a ON a.asset_id = o.asset_id
               WHERE o.observation_id = ?""", (observation_id,),
        ).fetchone()
        if observation is None:
            abort(404)
        corrections = conn.execute(
            """SELECT c.*, u.display_name AS created_by_name
               FROM observation_corrections c JOIN users u ON u.user_id = c.created_by
               WHERE c.observation_id = ? ORDER BY c.created_at""", (observation_id,),
        ).fetchall()
    return render_template("observation_detail.html", observation=observation, corrections=corrections)


@app.post("/observations/<observation_id>/corrections/new")
@roles_required(*OBSERVATION_CREATE_ROLES)
def create_observation_correction(observation_id: str) -> Response | tuple[str, int]:
    payload = request.form.to_dict()
    reason = payload.get("reason", "").strip()
    if not reason:
        return "Correction reason is required", 400
    try:
        value = float(payload.get("value", ""))
    except ValueError:
        return "Corrected value must be numeric", 400
    unit = payload.get("unit", "").strip()
    quality_flag = payload.get("quality_flag", "").strip()
    if not unit or quality_flag not in CORRECTION_QUALITY_FLAGS:
        return "Unit and a valid quality flag are required", 400
    correction_id = new_correction_id()
    with get_db() as conn:
        original = conn.execute(
            "SELECT observation_id FROM observations WHERE observation_id = ?", (observation_id,)
        ).fetchone()
        if original is None:
            abort(404)
        conn.execute(
            """INSERT INTO observation_corrections(
                   correction_id, observation_id, value, unit, quality_flag, notes,
                   reason, created_by, created_at
               ) VALUES(?,?,?,?,?,?,?,?,?)""",
            (correction_id, observation_id, value, unit, quality_flag,
             payload.get("notes", "").strip(), reason, g.user["user_id"], utc_now()),
        )
    record_audit_event(
        g.user["user_id"], "observation_corrected", "observation_correction", correction_id,
        json.dumps({"observation_id": observation_id, "reason": reason}),
    )
    flash("Correction added. The original observation was not changed.", "info")
    return redirect(url_for("observation_detail", observation_id=observation_id))


@app.get("/manual-work")
@roles_required(*TASK_VIEW_ROLES)
def manual_work() -> str:
    with get_db() as conn:
        tasks = conn.execute(
            """SELECT t.*, d.asset_id, d.experiment_id, d.assigned_user_id, d.due_at,
                      d.requires_approval, u.display_name AS assigned_user_name,
                      (SELECT decision FROM manual_task_approvals a WHERE a.task_id=t.task_id
                       ORDER BY reviewed_at DESC LIMIT 1) AS latest_decision
                 FROM manual_tasks t LEFT JOIN manual_task_details d ON d.task_id=t.task_id
                 LEFT JOIN users u ON u.user_id=d.assigned_user_id
                 ORDER BY CASE t.status WHEN 'open' THEN 0 WHEN 'in_progress' THEN 1 ELSE 2 END,
                          t.created_at DESC"""
        ).fetchall()
        plots = conn.execute("SELECT * FROM plots ORDER BY plot_id").fetchall()
        assets = conn.execute("SELECT * FROM assets WHERE status != 'retired' ORDER BY asset_id").fetchall()
        experiments = conn.execute("SELECT * FROM experiments WHERE status != 'cancelled' ORDER BY experiment_id").fetchall()
        users = conn.execute("SELECT * FROM users WHERE active=1 ORDER BY display_name").fetchall()
    return render_template("manual_work.html", tasks=tasks, plots=plots, assets=assets,
                           experiments=experiments, users=users)


@app.post("/manual-work")
@roles_required(*TASK_CREATE_ROLES)
def create_manual_task() -> Response | tuple[str, int]:
    form = request.form
    title = form.get("title", "").strip()
    task_type = form.get("task_type", "fieldwork").strip()
    priority = form.get("priority", "normal").strip()
    if not title or task_type not in TASK_TYPES or priority not in TASK_PRIORITIES:
        return "Title, valid work type, and valid priority are required", 400
    task_id = form.get("task_id", "").strip() or new_entity_id("TASK")
    plot_id = form.get("plot_id", "").strip() or None
    asset_id = form.get("asset_id", "").strip() or None
    experiment_id = form.get("experiment_id", "").strip() or None
    assigned_user_id = form.get("assigned_user_id", "").strip() or None
    with get_db() as conn:
        if plot_id and not plot_exists(conn, plot_id):
            return "Selected plot does not exist", 400
        for table, column, value, message in (
            ("assets", "asset_id", asset_id, "Selected asset does not exist"),
            ("experiments", "experiment_id", experiment_id, "Selected experiment does not exist"),
            ("users", "user_id", assigned_user_id, "Assigned user does not exist"),
        ):
            if value and conn.execute(f"SELECT 1 FROM {table} WHERE {column}=?", (value,)).fetchone() is None:
                return message, 400
        try:
            conn.execute("""INSERT INTO manual_tasks(task_id,title,task_type,plot_id,status,priority,assigned_to,notes,created_at)
                            VALUES(?,?,?,?,?,?,?,?,?)""",
                         (task_id, title, task_type, plot_id, "open", priority,
                          form.get("assigned_to", "").strip(), form.get("notes", "").strip(), utc_now()))
            conn.execute("""INSERT INTO manual_task_details(task_id,asset_id,experiment_id,assigned_user_id,due_at,requires_approval,created_by)
                            VALUES(?,?,?,?,?,?,?)""",
                         (task_id, asset_id, experiment_id, assigned_user_id,
                          form.get("due_at", "").strip() or None,
                          1 if form.get("requires_approval") else 0, g.user["user_id"]))
        except sqlite3.IntegrityError:
            return "Task ID already exists or a linked record is invalid", 400
    record_audit_event(g.user["user_id"], "manual_task_created", "manual_task", task_id,
                       json.dumps({"plot_id": plot_id, "asset_id": asset_id, "experiment_id": experiment_id}))
    return redirect(url_for("manual_task_detail", task_id=task_id))


@app.get("/manual-work/<task_id>")
@roles_required(*TASK_VIEW_ROLES)
def manual_task_detail(task_id: str) -> str:
    with get_db() as conn:
        task = conn.execute("""SELECT t.*, d.asset_id, d.experiment_id, d.assigned_user_id, d.due_at,
                                      d.requires_approval, u.display_name AS assigned_user_name
                                 FROM manual_tasks t LEFT JOIN manual_task_details d ON d.task_id=t.task_id
                                 LEFT JOIN users u ON u.user_id=d.assigned_user_id WHERE t.task_id=?""", (task_id,)).fetchone()
        if task is None:
            abort(404)
        history = conn.execute("SELECT * FROM manual_task_status_history WHERE task_id=? ORDER BY changed_at DESC", (task_id,)).fetchall()
        evidence = conn.execute("SELECT * FROM manual_task_evidence WHERE task_id=? ORDER BY recorded_at DESC", (task_id,)).fetchall()
        approvals = conn.execute("SELECT * FROM manual_task_approvals WHERE task_id=? ORDER BY reviewed_at DESC", (task_id,)).fetchall()
    return render_template("manual_task_detail.html", task=task, history=history, evidence=evidence,
                           approvals=approvals, statuses=sorted(TASK_STATUSES))


@app.post("/manual-work/<task_id>/status")
@roles_required(*TASK_WORK_ROLES)
def change_manual_task_status(task_id: str) -> Response | tuple[str, int]:
    new_status = request.form.get("status", "").strip()
    reason = request.form.get("reason", "").strip()
    if new_status not in TASK_STATUSES or not reason:
        return "Valid status and reason are required", 400
    with get_db() as conn:
        task = conn.execute("SELECT * FROM manual_tasks WHERE task_id=?", (task_id,)).fetchone()
        if task is None:
            abort(404)
        if new_status == "completed":
            detail = conn.execute("SELECT * FROM manual_task_details WHERE task_id=?", (task_id,)).fetchone()
            if detail and detail["requires_approval"]:
                approved = conn.execute("SELECT 1 FROM manual_task_approvals WHERE task_id=? AND decision='approved'", (task_id,)).fetchone()
                if approved is None:
                    return "This task requires approval before completion", 400
        now = utc_now()
        conn.execute("UPDATE manual_tasks SET status=?, completed_at=? WHERE task_id=?",
                     (new_status, now if new_status == "completed" else None, task_id))
        conn.execute("""INSERT INTO manual_task_status_history(status_event_id,task_id,previous_status,new_status,reason,changed_by,changed_at)
                        VALUES(?,?,?,?,?,?,?)""",
                     (new_entity_id("TASKSTATUS"), task_id, task["status"], new_status, reason, g.user["user_id"], now))
    record_audit_event(g.user["user_id"], "manual_task_status_changed", "manual_task", task_id,
                       json.dumps({"from": task["status"], "to": new_status, "reason": reason}))
    return redirect(url_for("manual_task_detail", task_id=task_id))


@app.post("/manual-work/<task_id>/evidence")
@roles_required(*TASK_WORK_ROLES)
def add_manual_task_evidence(task_id: str) -> Response | tuple[str, int]:
    evidence_type = request.form.get("evidence_type", "").strip()
    reference = request.form.get("reference", "").strip()
    if evidence_type not in {"observation", "photo", "file", "note"} or not reference:
        return "Valid evidence type and reference are required", 400
    evidence_id = new_entity_id("EVID")
    with get_db() as conn:
        if conn.execute("SELECT 1 FROM manual_tasks WHERE task_id=?", (task_id,)).fetchone() is None:
            abort(404)
        if evidence_type == "observation" and conn.execute("SELECT 1 FROM observations WHERE observation_id=?", (reference,)).fetchone() is None:
            return "Referenced observation does not exist", 400
        conn.execute("""INSERT INTO manual_task_evidence(evidence_id,task_id,evidence_type,reference,notes,recorded_by,recorded_at)
                        VALUES(?,?,?,?,?,?,?)""", (evidence_id, task_id, evidence_type, reference,
                        request.form.get("notes", "").strip(), g.user["user_id"], utc_now()))
    record_audit_event(g.user["user_id"], "manual_task_evidence_added", "manual_task_evidence", evidence_id,
                       json.dumps({"task_id": task_id, "evidence_type": evidence_type}))
    return redirect(url_for("manual_task_detail", task_id=task_id))


@app.post("/manual-work/<task_id>/approval")
@roles_required(*TASK_APPROVAL_ROLES)
def review_manual_task(task_id: str) -> Response | tuple[str, int]:
    decision = request.form.get("decision", "").strip()
    reason = request.form.get("reason", "").strip()
    if decision not in {"approved", "rejected"} or not reason:
        return "Valid decision and reason are required", 400
    approval_id = new_entity_id("TASKAPP")
    with get_db() as conn:
        if conn.execute("SELECT 1 FROM manual_tasks WHERE task_id=?", (task_id,)).fetchone() is None:
            abort(404)
        conn.execute("""INSERT INTO manual_task_approvals(approval_id,task_id,decision,reason,reviewer_id,reviewed_at)
                        VALUES(?,?,?,?,?,?)""", (approval_id, task_id, decision, reason, g.user["user_id"], utc_now()))
    record_audit_event(g.user["user_id"], "manual_task_reviewed", "manual_task_approval", approval_id,
                       json.dumps({"task_id": task_id, "decision": decision}))
    return redirect(url_for("manual_task_detail", task_id=task_id))


@app.post("/manual-work/<task_id>/complete")
@roles_required("administrator", "field_operator")
def complete_manual_task(task_id: str) -> Response:
    return change_manual_task_status(task_id)


@app.get("/registry")
@roles_required("administrator", "researcher", "field_operator", "viewer")
def registry() -> str:
    with get_db() as conn:
        plots = conn.execute("SELECT * FROM plots ORDER BY plot_id").fetchall()
        assets = conn.execute("SELECT * FROM assets ORDER BY asset_id").fetchall()
        experiments = conn.execute("SELECT * FROM experiments ORDER BY experiment_id").fetchall()
    return render_template("registry.html", plots=plots, assets=assets, experiments=experiments)


@app.route("/plots/new", methods=["GET", "POST"])
@roles_required(*REGISTRY_EDIT_ROLES)
def create_plot() -> str | Response:
    values = request.form.to_dict() if request.method == "POST" else {"status": "Active"}
    if request.method == "POST":
        errors = validate_plot_payload(values)
        plot_id = values.get("plot_id", "").strip() or new_plot_id()
        if not errors:
            try:
                with get_db() as conn:
                    conn.execute(
                        """INSERT INTO plots(plot_id, name, plot_type, area, status, created_at)
                           VALUES(?,?,?,?,?,?)""",
                        (
                            plot_id,
                            values["name"].strip(),
                            values["plot_type"].strip(),
                            values.get("area", "").strip(),
                            values["status"].strip(),
                            utc_now(),
                        ),
                    )
            except sqlite3.IntegrityError:
                errors.append("That plot ID already exists.")
            else:
                record_audit_event(
                    g.user["user_id"], "plot_created", "plot", plot_id,
                    json.dumps({"name": values["name"].strip(), "status": values["status"]}),
                )
                flash("Plot created.", "info")
                return redirect(url_for("plot_detail", plot_id=plot_id))
        for error in errors:
            flash(error, "error")
    return render_template(
        "plot_form.html", values=values, plot=None, plot_types=sorted(PLOT_TYPES),
        statuses=sorted(PLOT_STATUSES),
    )


@app.get("/plots/<plot_id>")
@roles_required(*REGISTRY_VIEW_ROLES)
def plot_detail(plot_id: str) -> str:
    with get_db() as conn:
        plot = get_plot(conn, plot_id)
        if plot is None:
            abort(404)
        assets = conn.execute(
            "SELECT * FROM assets WHERE plot_id = ? ORDER BY asset_id", (plot_id,)
        ).fetchall()
        experiments = conn.execute(
            "SELECT * FROM experiments WHERE plot_id = ? ORDER BY created_at DESC", (plot_id,)
        ).fetchall()
        observations = conn.execute(
            """SELECT * FROM observations WHERE plot_id = ?
               ORDER BY observed_at DESC LIMIT 10""",
            (plot_id,),
        ).fetchall()
    return render_template(
        "plot_detail.html", plot=plot, assets=assets, experiments=experiments,
        observations=observations,
    )


@app.route("/plots/<plot_id>/edit", methods=["GET", "POST"])
@roles_required(*REGISTRY_EDIT_ROLES)
def edit_plot(plot_id: str) -> str | Response:
    with get_db() as conn:
        plot = get_plot(conn, plot_id)
    if plot is None:
        abort(404)
    values = request.form.to_dict() if request.method == "POST" else dict(plot)
    if request.method == "POST":
        errors = validate_plot_payload(values)
        if not errors:
            with get_db() as conn:
                conn.execute(
                    """UPDATE plots SET name = ?, plot_type = ?, area = ?, status = ?
                       WHERE plot_id = ?""",
                    (
                        values["name"].strip(), values["plot_type"].strip(),
                        values.get("area", "").strip(), values["status"].strip(), plot_id,
                    ),
                )
            record_audit_event(
                g.user["user_id"], "plot_updated", "plot", plot_id,
                json.dumps({"before": dict(plot), "after": values}),
            )
            flash("Plot updated.", "info")
            return redirect(url_for("plot_detail", plot_id=plot_id))
        for error in errors:
            flash(error, "error")
    return render_template(
        "plot_form.html", values=values, plot=plot, plot_types=sorted(PLOT_TYPES),
        statuses=sorted(PLOT_STATUSES),
    )


@app.post("/plots/<plot_id>/retire")
@roles_required(*REGISTRY_RETIRE_ROLES)
def retire_plot(plot_id: str) -> Response:
    with get_db() as conn:
        plot = get_plot(conn, plot_id)
        if plot is None:
            abort(404)
        blockers = plot_retire_blockers(conn, plot_id)
        if blockers:
            for blocker in blockers:
                flash(f"Plot cannot be retired: {blocker}.", "error")
            return redirect(url_for("plot_detail", plot_id=plot_id))
        conn.execute("UPDATE plots SET status = 'Retired' WHERE plot_id = ?", (plot_id,))
    record_audit_event(
        g.user["user_id"], "plot_retired", "plot", plot_id,
        json.dumps({"previous_status": plot["status"], "status": "Retired"}),
    )
    flash("Plot retired. Its history remains available.", "info")
    return redirect(url_for("plot_detail", plot_id=plot_id))


@app.route("/assets/new", methods=["GET", "POST"])
@roles_required(*REGISTRY_EDIT_ROLES)
def create_asset() -> str | Response:
    values = request.form.to_dict() if request.method == "POST" else {
        "status": "available", "revision": "rev-a"
    }
    with get_db() as conn:
        plots = conn.execute("SELECT * FROM plots ORDER BY plot_id").fetchall()
        if request.method == "POST":
            errors = validate_asset_payload(conn, values)
        else:
            errors = []
    if request.method == "POST":
        asset_id = values.get("asset_id", "").strip() or new_asset_id()
        if not errors:
            try:
                with get_db() as conn:
                    conn.execute(
                        """INSERT INTO assets(
                               asset_id, name, asset_type, plot_id, status, revision, created_at
                           ) VALUES(?,?,?,?,?,?,?)""",
                        (
                            asset_id, values["name"].strip(), values["asset_type"].strip(),
                            values.get("plot_id", "").strip() or None,
                            values["status"].strip(), "rev-a", utc_now(),
                        ),
                    )
            except sqlite3.IntegrityError:
                errors.append("That asset ID already exists or its plot assignment is invalid.")
            else:
                record_audit_event(
                    g.user["user_id"], "asset_created", "asset", asset_id,
                    json.dumps({"name": values["name"].strip(), "plot_id": values.get("plot_id")}),
                )
                flash("Asset created.", "info")
                return redirect(url_for("asset_detail", asset_id=asset_id))
        for error in errors:
            flash(error, "error")
    return render_template(
        "asset_form.html", values=values, asset=None, plots=plots,
        statuses=sorted(ASSET_STATUSES),
    )


@app.get("/assets/<asset_id>")
@roles_required(*REGISTRY_VIEW_ROLES)
def asset_detail(asset_id: str) -> str:
    with get_db() as conn:
        asset = conn.execute(
            """SELECT a.*, p.name AS plot_name FROM assets a
               LEFT JOIN plots p ON p.plot_id = a.plot_id WHERE a.asset_id = ?""",
            (asset_id,),
        ).fetchone()
        if asset is None:
            abort(404)
        observations = conn.execute(
            """SELECT * FROM observations WHERE asset_id = ?
               ORDER BY observed_at DESC LIMIT 10""",
            (asset_id,),
        ).fetchall()
    return render_template("asset_detail.html", asset=asset, observations=observations)


@app.route("/assets/<asset_id>/edit", methods=["GET", "POST"])
@roles_required(*REGISTRY_EDIT_ROLES)
def edit_asset(asset_id: str) -> str | Response:
    with get_db() as conn:
        asset = get_asset(conn, asset_id)
        if asset is None:
            abort(404)
        plots = conn.execute("SELECT * FROM plots ORDER BY plot_id").fetchall()
    values = request.form.to_dict() if request.method == "POST" else dict(asset)
    if request.method == "POST":
        with get_db() as conn:
            errors = validate_asset_payload(conn, values)
        if not errors:
            changed = any(
                (values.get(field, "").strip() or None) != (asset[field] or None)
                for field in ("name", "asset_type", "plot_id", "status")
            )
            revision = next_revision(asset["revision"]) if changed else asset["revision"]
            with get_db() as conn:
                conn.execute(
                    """UPDATE assets SET name = ?, asset_type = ?, plot_id = ?,
                       status = ?, revision = ? WHERE asset_id = ?""",
                    (
                        values["name"].strip(), values["asset_type"].strip(),
                        values.get("plot_id", "").strip() or None,
                        values["status"].strip(), revision, asset_id,
                    ),
                )
            record_audit_event(
                g.user["user_id"], "asset_updated", "asset", asset_id,
                json.dumps({"before": dict(asset), "after": values, "revision": revision}),
            )
            flash("Asset updated.", "info")
            return redirect(url_for("asset_detail", asset_id=asset_id))
        for error in errors:
            flash(error, "error")
    return render_template(
        "asset_form.html", values=values, asset=asset, plots=plots,
        statuses=sorted(ASSET_STATUSES),
    )


@app.post("/assets/<asset_id>/retire")
@roles_required(*REGISTRY_RETIRE_ROLES)
def retire_asset(asset_id: str) -> Response:
    with get_db() as conn:
        asset = get_asset(conn, asset_id)
        if asset is None:
            abort(404)
        revision = next_revision(asset["revision"])
        conn.execute(
            "UPDATE assets SET status = 'retired', revision = ? WHERE asset_id = ?",
            (revision, asset_id),
        )
    record_audit_event(
        g.user["user_id"], "asset_retired", "asset", asset_id,
        json.dumps({"previous_status": asset["status"], "revision": revision}),
    )
    flash("Asset retired. Its history remains available.", "info")
    return redirect(url_for("asset_detail", asset_id=asset_id))


@app.get("/recommendations")
@roles_required("administrator", "researcher")
def recommendations() -> str:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM recommendations ORDER BY created_at DESC").fetchall()
    return render_template("recommendations.html", recommendations=rows)


@app.get("/experiments")
@roles_required(*EXPERIMENT_VIEW_ROLES)
def experiments() -> str:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT e.*, p.name AS plot_name,
                      (SELECT COUNT(*) FROM treatments t WHERE t.experiment_id=e.experiment_id) AS treatment_count,
                      (SELECT COUNT(*) FROM treatment_assignments a WHERE a.experiment_id=e.experiment_id) AS assignment_count
               FROM experiments e LEFT JOIN plots p ON p.plot_id=e.plot_id
               ORDER BY e.created_at DESC"""
        ).fetchall()
    return render_template("experiments.html", experiments=rows)


@app.route("/experiments/new", methods=["GET", "POST"])
@roles_required(*EXPERIMENT_EDIT_ROLES)
def create_experiment() -> str | Response:
    values = request.form.to_dict() if request.method == "POST" else {"status": "draft"}
    with get_db() as conn:
        plots = conn.execute("SELECT * FROM plots WHERE status='Active' ORDER BY plot_id").fetchall()
        errors = validate_experiment_payload(conn, values) if request.method == "POST" else []
    if request.method == "POST" and not errors:
        experiment_id = values.get("experiment_id", "").strip() or new_entity_id("EXP")
        try:
            with get_db() as conn:
                conn.execute(
                    """INSERT INTO experiments(experiment_id,title,hypothesis,status,plot_id,owner,created_at)
                       VALUES(?,?,?,?,?,?,?)""",
                    (experiment_id, values["title"].strip(), values["hypothesis"].strip(),
                     values["status"].strip(), values.get("plot_id", "").strip() or None,
                     g.user["user_id"], utc_now()),
                )
        except sqlite3.IntegrityError:
            errors.append("That experiment ID already exists or a linked record is invalid.")
        else:
            record_audit_event(g.user["user_id"], "experiment_created", "experiment", experiment_id, json.dumps(values))
            return redirect(url_for("experiment_detail", experiment_id=experiment_id))
    for error in errors:
        flash(error, "error")
    return render_template("experiment_form.html", values=values, plots=plots, statuses=sorted(EXPERIMENT_STATUSES))


@app.get("/experiments/<experiment_id>")
@roles_required(*EXPERIMENT_VIEW_ROLES)
def experiment_detail(experiment_id: str) -> str:
    with get_db() as conn:
        experiment = conn.execute("SELECT * FROM experiments WHERE experiment_id=?", (experiment_id,)).fetchone()
        if experiment is None:
            abort(404)
        treatments = conn.execute("SELECT * FROM treatments WHERE experiment_id=? ORDER BY created_at", (experiment_id,)).fetchall()
        assignments = conn.execute(
            """SELECT a.*, t.name AS treatment_name, p.name AS plot_name, u.display_name AS responsible_name
               FROM treatment_assignments a JOIN treatments t ON t.treatment_id=a.treatment_id
               JOIN plots p ON p.plot_id=a.plot_id JOIN users u ON u.user_id=a.responsible_user_id
               WHERE a.experiment_id=? ORDER BY a.assigned_at""", (experiment_id,)
        ).fetchall()
        history = conn.execute("SELECT * FROM experiment_status_history WHERE experiment_id=? ORDER BY changed_at DESC", (experiment_id,)).fetchall()
        outcomes = conn.execute(
            """SELECT o.*, ob.observed_property, ob.value, ob.unit FROM experiment_outcomes o
               JOIN observations ob ON ob.observation_id=o.observation_id
               WHERE o.experiment_id=? ORDER BY o.recorded_at DESC""", (experiment_id,)
        ).fetchall()
        plots = conn.execute("SELECT * FROM plots WHERE status='Active' ORDER BY plot_id").fetchall()
        users = conn.execute("SELECT * FROM users WHERE active=1 ORDER BY display_name").fetchall()
        observations = conn.execute("SELECT * FROM observations ORDER BY observed_at DESC").fetchall()
    return render_template("experiment_detail.html", experiment=experiment, treatments=treatments,
        assignments=assignments, history=history, outcomes=outcomes, plots=plots, users=users,
        observations=observations, statuses=sorted(EXPERIMENT_STATUSES))


@app.post("/experiments/<experiment_id>/treatments")
@roles_required(*EXPERIMENT_EDIT_ROLES)
def add_treatment(experiment_id: str) -> Response | tuple[str, int]:
    name = request.form.get("name", "").strip()
    if not name:
        return "Treatment name is required", 400
    treatment_id = request.form.get("treatment_id", "").strip() or new_entity_id("TRT")
    try:
        with get_db() as conn:
            if conn.execute("SELECT 1 FROM experiments WHERE experiment_id=?", (experiment_id,)).fetchone() is None:
                abort(404)
            conn.execute("""INSERT INTO treatments(treatment_id,experiment_id,name,description,is_control,created_by,created_at)
                            VALUES(?,?,?,?,?,?,?)""", (treatment_id, experiment_id, name,
                            request.form.get("description", "").strip(), 1 if request.form.get("is_control") else 0,
                            g.user["user_id"], utc_now()))
    except sqlite3.IntegrityError:
        return "Treatment ID already exists or is invalid", 400
    record_audit_event(g.user["user_id"], "treatment_created", "treatment", treatment_id, json.dumps({"experiment_id": experiment_id}))
    return redirect(url_for("experiment_detail", experiment_id=experiment_id))


@app.post("/experiments/<experiment_id>/assignments")
@roles_required(*EXPERIMENT_EDIT_ROLES)
def add_treatment_assignment(experiment_id: str) -> Response | tuple[str, int]:
    assignment_id = request.form.get("assignment_id", "").strip() or new_entity_id("ASN")
    treatment_id = request.form.get("treatment_id", "").strip()
    plot_id = request.form.get("plot_id", "").strip()
    responsible = request.form.get("responsible_user_id", "").strip()
    try:
        with get_db() as conn:
            treatment = conn.execute("SELECT * FROM treatments WHERE treatment_id=? AND experiment_id=?", (treatment_id, experiment_id)).fetchone()
            if treatment is None:
                return "Treatment does not belong to this experiment", 400
            conn.execute("""INSERT INTO treatment_assignments(assignment_id,experiment_id,treatment_id,plot_id,responsible_user_id,assigned_at,start_date,end_date,notes)
                            VALUES(?,?,?,?,?,?,?,?,?)""", (assignment_id, experiment_id, treatment_id, plot_id, responsible,
                            utc_now(), request.form.get("start_date") or None, request.form.get("end_date") or None,
                            request.form.get("notes", "").strip()))
    except sqlite3.IntegrityError:
        return "Assignment is invalid, duplicated, or references a missing record", 400
    record_audit_event(g.user["user_id"], "treatment_assigned", "treatment_assignment", assignment_id, json.dumps({"experiment_id": experiment_id, "plot_id": plot_id}))
    return redirect(url_for("experiment_detail", experiment_id=experiment_id))


@app.post("/experiments/<experiment_id>/status")
@roles_required(*EXPERIMENT_EDIT_ROLES)
def change_experiment_status(experiment_id: str) -> Response | tuple[str, int]:
    new_status = request.form.get("status", "").strip()
    reason = request.form.get("reason", "").strip()
    if new_status not in EXPERIMENT_STATUSES or not reason:
        return "Valid status and reason are required", 400
    with get_db() as conn:
        experiment = conn.execute("SELECT * FROM experiments WHERE experiment_id=?", (experiment_id,)).fetchone()
        if experiment is None:
            abort(404)
        event_id = new_entity_id("STATUS")
        conn.execute("UPDATE experiments SET status=? WHERE experiment_id=?", (new_status, experiment_id))
        conn.execute("""INSERT INTO experiment_status_history(status_event_id,experiment_id,previous_status,new_status,reason,changed_by,changed_at)
                        VALUES(?,?,?,?,?,?,?)""", (event_id, experiment_id, experiment["status"], new_status, reason, g.user["user_id"], utc_now()))
    record_audit_event(g.user["user_id"], "experiment_status_changed", "experiment", experiment_id,
                       json.dumps({"from": experiment["status"], "to": new_status, "reason": reason}))
    return redirect(url_for("experiment_detail", experiment_id=experiment_id))


@app.post("/experiments/<experiment_id>/outcomes")
@roles_required(*EXPERIMENT_EDIT_ROLES)
def add_experiment_outcome(experiment_id: str) -> Response | tuple[str, int]:
    outcome_id = new_entity_id("OUT")
    observation_id = request.form.get("observation_id", "").strip()
    assignment_id = request.form.get("assignment_id", "").strip() or None
    try:
        with get_db() as conn:
            if assignment_id and conn.execute("SELECT 1 FROM treatment_assignments WHERE assignment_id=? AND experiment_id=?", (assignment_id, experiment_id)).fetchone() is None:
                return "Assignment does not belong to this experiment", 400
            conn.execute("""INSERT INTO experiment_outcomes(outcome_id,experiment_id,assignment_id,observation_id,interpretation,recorded_by,recorded_at)
                            VALUES(?,?,?,?,?,?,?)""", (outcome_id, experiment_id, assignment_id, observation_id,
                            request.form.get("interpretation", "").strip(), g.user["user_id"], utc_now()))
    except sqlite3.IntegrityError:
        return "Outcome is duplicated or references a missing record", 400
    record_audit_event(g.user["user_id"], "experiment_outcome_linked", "experiment_outcome", outcome_id, json.dumps({"experiment_id": experiment_id, "observation_id": observation_id}))
    return redirect(url_for("experiment_detail", experiment_id=experiment_id))


@app.post("/recommendations/<recommendation_id>/decision")
@roles_required("administrator", "researcher")
def recommendation_decision(recommendation_id: str) -> tuple[str, int] | Response:
    decision = request.form.get("decision")
    if decision not in {"approved", "rejected", "edited"}:
        return "Invalid decision", 400
    with get_db() as conn:
        conn.execute(
            """UPDATE recommendations
               SET approval_status=?, decided_by=?, decision_notes=?, decided_at=?
               WHERE recommendation_id=?""",
            (
                decision,
                request.form.get("decided_by", "Field reviewer"),
                request.form.get("decision_notes", ""),
                utc_now(),
                recommendation_id,
            ),
        )
    return redirect(url_for("recommendations"))


@app.get("/api/health")
def health() -> Response:
    return jsonify({"status": "ok", "time": utc_now(), "mode": "manual-first"})


@app.get("/api/export/<entity>.csv")
@roles_required("administrator", "researcher")
def export_csv(entity: str) -> tuple[str, int] | Response:
    allowed = {
        "plots": "SELECT * FROM plots ORDER BY plot_id",
        "assets": "SELECT * FROM assets ORDER BY asset_id",
        "observations": "SELECT * FROM observations ORDER BY observed_at",
        "observation_corrections": "SELECT * FROM observation_corrections ORDER BY created_at",
        "manual_tasks": "SELECT * FROM manual_tasks ORDER BY created_at",
        "manual_task_details": "SELECT * FROM manual_task_details ORDER BY task_id",
        "manual_task_status_history": "SELECT * FROM manual_task_status_history ORDER BY changed_at",
        "manual_task_evidence": "SELECT * FROM manual_task_evidence ORDER BY recorded_at",
        "manual_task_approvals": "SELECT * FROM manual_task_approvals ORDER BY reviewed_at",
        "experiments": "SELECT * FROM experiments ORDER BY experiment_id",
        "treatments": "SELECT * FROM treatments ORDER BY treatment_id",
        "treatment_assignments": "SELECT * FROM treatment_assignments ORDER BY assignment_id",
        "experiment_status_history": "SELECT * FROM experiment_status_history ORDER BY changed_at",
        "experiment_outcomes": "SELECT * FROM experiment_outcomes ORDER BY recorded_at",
        "recommendations": "SELECT * FROM recommendations ORDER BY created_at",
    }
    if entity not in allowed:
        return "Unknown export entity", 404
    with get_db() as conn:
        rows = conn.execute(allowed[entity]).fetchall()
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows([dict(row) for row in rows])
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={entity}.csv"},
    )


@app.get("/api/export/all.json")
@roles_required("administrator", "researcher")
def export_json() -> Response:
    entities = [
        "plots", "assets", "observations", "observation_corrections",
        "manual_tasks", "manual_task_details", "manual_task_status_history",
        "manual_task_evidence", "manual_task_approvals", "experiments", "treatments", "treatment_assignments",
        "experiment_status_history", "experiment_outcomes", "recommendations",
    ]
    data: dict[str, list[dict[str, Any]]] = {}
    with get_db() as conn:
        for entity in entities:
            rows = conn.execute(f"SELECT * FROM {entity}").fetchall()
            data[entity] = [dict(row) for row in rows]
    return jsonify({"exported_at": utc_now(), "data": data})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
