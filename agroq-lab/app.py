from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Iterator
import csv
import io
import json
import os
import sqlite3
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

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
app.secret_key = os.environ.get("AGROQ_SECRET_KEY", DEV_SECRET_KEY)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_audit_id() -> str:
    return f"AGQ-AUDIT-{int(datetime.now().timestamp() * 1000)}"


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
@roles_required("administrator", "researcher", "field_operator")
def new_observation() -> str | Response:
    if request.method == "POST":
        payload = request.form.to_dict()
        create_observation(payload)
        return redirect(url_for("dashboard"))
    with get_db() as conn:
        plots = conn.execute("SELECT * FROM plots ORDER BY plot_id").fetchall()
        assets = conn.execute("SELECT * FROM assets ORDER BY asset_id").fetchall()
    return render_template("observation_form.html", plots=plots, assets=assets)


def create_observation(payload: dict[str, Any]) -> str:
    required = ["plot_id", "observed_property", "value", "unit", "source_type"]
    missing = [key for key in required if payload.get(key) in (None, "")]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
    observation_id = payload.get("observation_id") or f"AGQ-OBS-{int(datetime.now().timestamp() * 1000)}"
    observed_at = payload.get("observed_at") or utc_now()
    with get_db() as conn:
        conn.execute(
            """INSERT INTO observations(
                observation_id, plot_id, asset_id, observed_property, value, unit,
                source_type, quality_flag, notes, observed_at, created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (
                observation_id,
                payload["plot_id"],
                payload.get("asset_id") or None,
                payload["observed_property"],
                float(payload["value"]),
                payload["unit"],
                payload["source_type"],
                payload.get("quality_flag", "unverified"),
                payload.get("notes", ""),
                observed_at,
                utc_now(),
            ),
        )
    return observation_id


@app.post("/api/observations")
@roles_required("administrator", "researcher", "field_operator")
def api_create_observation() -> tuple[Response, int] | Response:
    payload = request.get_json(silent=True) or {}
    try:
        observation_id = create_observation(payload)
    except (ValueError, sqlite3.IntegrityError) as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": True, "observation_id": observation_id}), 201


@app.get("/manual-work")
@roles_required("administrator", "field_operator")
def manual_work() -> str:
    with get_db() as conn:
        tasks = conn.execute(
            "SELECT * FROM manual_tasks ORDER BY CASE status WHEN 'open' THEN 0 ELSE 1 END, created_at DESC"
        ).fetchall()
        plots = conn.execute("SELECT * FROM plots ORDER BY plot_id").fetchall()
    return render_template("manual_work.html", tasks=tasks, plots=plots)


@app.post("/manual-work")
@roles_required("administrator", "field_operator")
def create_manual_task() -> Response:
    form = request.form
    task_id = f"AGQ-TASK-{int(datetime.now().timestamp() * 1000)}"
    with get_db() as conn:
        conn.execute(
            """INSERT INTO manual_tasks(
                task_id, title, task_type, plot_id, status, priority, assigned_to, notes, created_at
            ) VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                task_id,
                form["title"],
                form.get("task_type", "fieldwork"),
                form.get("plot_id") or None,
                "open",
                form.get("priority", "normal"),
                form.get("assigned_to", ""),
                form.get("notes", ""),
                utc_now(),
            ),
        )
    return redirect(url_for("manual_work"))


@app.post("/manual-work/<task_id>/complete")
@roles_required("administrator", "field_operator")
def complete_manual_task(task_id: str) -> Response:
    with get_db() as conn:
        conn.execute(
            "UPDATE manual_tasks SET status='completed', completed_at=? WHERE task_id=?",
            (utc_now(), task_id),
        )
    return redirect(url_for("manual_work"))


@app.get("/registry")
@roles_required("administrator", "researcher", "field_operator", "viewer")
def registry() -> str:
    with get_db() as conn:
        plots = conn.execute("SELECT * FROM plots ORDER BY plot_id").fetchall()
        assets = conn.execute("SELECT * FROM assets ORDER BY asset_id").fetchall()
        experiments = conn.execute("SELECT * FROM experiments ORDER BY experiment_id").fetchall()
    return render_template("registry.html", plots=plots, assets=assets, experiments=experiments)


@app.get("/recommendations")
@roles_required("administrator", "researcher")
def recommendations() -> str:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM recommendations ORDER BY created_at DESC").fetchall()
    return render_template("recommendations.html", recommendations=rows)


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
        "manual_tasks": "SELECT * FROM manual_tasks ORDER BY created_at",
        "experiments": "SELECT * FROM experiments ORDER BY experiment_id",
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
    entities = ["plots", "assets", "observations", "manual_tasks", "experiments", "recommendations"]
    data: dict[str, list[dict[str, Any]]] = {}
    with get_db() as conn:
        for entity in entities:
            rows = conn.execute(f"SELECT * FROM {entity}").fetchall()
            data[entity] = [dict(row) for row in rows]
    return jsonify({"exported_at": utc_now(), "data": data})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
