from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import secrets
import threading
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Blueprint, Response, g, jsonify, render_template, request, session

BASE_DIR = Path(__file__).resolve().parent
NCBI_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ALLOWED_DATABASES = frozenset({"nuccore", "protein"})
ALLOWED_EXPORTS = frozenset({"fasta", "json", "csv"})
ACCESSION_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,80}$")
NUCLEOTIDE_ALPHABET = frozenset("ACGTRYSWKMBDHVNU")
PROTEIN_ALPHABET = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ*")
_RATE_LOCK = threading.Lock()
_LAST_REQUEST_AT = 0.0

DEMO_EXPERIMENTS: tuple[dict[str, Any], ...] = (
    {
        "experiment_id": "AGQ-PHENO-001",
        "title": "Slobolt Lettuce Low-Water Biomass-Retention Phenotype",
        "hypothesis": "Under a synthetic moderate low-water scenario, Slobolt lettuce will retain measurable leafy biomass relative to a full-irrigation control.",
        "status": "active",
        "plot_id": "AGQ-PLOT-002",
        "owner": "Othon Reyes Jr.",
        "demo_class": "phenotype",
        "organism": "Lactuca sativa L.",
        "cultivar": "Slobolt",
        "objective": "Demonstrate the observation-to-decision workflow for a candidate low-water biomass-retention phenotype.",
        "design": {
            "duration_days": 21,
            "groups": [
                {"name": "Low-water treatment", "plot_id": "AGQ-PLOT-002", "irrigation_percent_of_control": 70, "synthetic_plants": 6, "is_control": False},
                {"name": "Full-irrigation control", "plot_id": "AGQ-PLOT-001", "irrigation_percent_of_control": 100, "synthetic_plants": 6, "is_control": True},
            ],
            "approval_sequence": ["Protocol review", "Synthetic activation approval", "Observation review", "Outcome interpretation approval", "Export and archive"],
        },
        "primary_outcome": "Fresh shoot biomass",
        "secondary_outcomes": ["Canopy area", "Leaf count", "Wilting score", "Root-zone moisture", "Apparent irrigation productivity"],
        "sample_plan": {"baseline": "Day 0", "checkpoints": ["Day 7", "Day 14", "Day 21"], "evidence": ["manual observation", "synthetic scenario", "exported report"]},
        "approval_state": "approved_for_demo",
        "evidence_mode": "synthetic",
        "limitations": "Synthetic software demonstration only. Exact seed lineage and genotype markers are not verified. No dominant, recessive, causal, or new-variety claim is made.",
    },
    {
        "experiment_id": "AGQ-PHENO-002",
        "title": "Slobolt Lettuce Heat-Resilience and Bolting-Delay Phenotype",
        "hypothesis": "A candidate heat-resilience workflow can distinguish canopy retention and bolting-related responses between a synthetic warm-condition group and a synthetic baseline group.",
        "status": "planned",
        "plot_id": "AGQ-PLOT-003",
        "owner": "Othon Reyes Jr.",
        "demo_class": "phenotype",
        "organism": "Lactuca sativa L.",
        "cultivar": "Slobolt",
        "objective": "Demonstrate a second phenotype experiment with human approval, scheduled observations, and auditable comparison against a control.",
        "design": {
            "duration_days": 14,
            "groups": [
                {"name": "Synthetic warm-condition treatment", "plot_id": "AGQ-PLOT-003", "scenario_label": "elevated daytime temperature", "synthetic_plants": 6, "is_control": False},
                {"name": "Synthetic baseline control", "plot_id": "AGQ-PLOT-001", "scenario_label": "baseline operations", "synthetic_plants": 6, "is_control": True},
            ],
            "approval_sequence": ["Protocol review", "Scenario-boundary approval", "Observation review", "Outcome interpretation approval", "Export and archive"],
        },
        "primary_outcome": "Bolting-delay score",
        "secondary_outcomes": ["Canopy area retention", "Leaf count", "Fresh shoot biomass", "Wilting score", "Time-to-review trigger"],
        "sample_plan": {"baseline": "Day 0", "checkpoints": ["Day 3", "Day 7", "Day 10", "Day 14"], "evidence": ["manual observation", "synthetic heat scenario", "approval history"]},
        "approval_state": "pending_review",
        "evidence_mode": "synthetic",
        "limitations": "Synthetic scenario for workflow validation. It does not establish a heat-tolerant variety or a verified biological performance claim.",
    },
    {
        "experiment_id": "AGQ-GENO-003",
        "title": "Lettuce Candidate Sequence-to-Pigmentation Evidence Map",
        "hypothesis": "Public nucleotide and protein records can be retrieved, preserved with provenance, linked to a candidate pigmentation phenotype, and reviewed without treating a database association as proof of causality.",
        "status": "draft",
        "plot_id": None,
        "owner": "Othon Reyes Jr.",
        "demo_class": "genotype_to_phenotype",
        "organism": "Lactuca sativa L.",
        "cultivar": "Candidate comparison set",
        "objective": "Demonstrate push-button DNA/protein lookup, one-click insertion, sequence-to-experiment linking, provenance, review, and export.",
        "design": {
            "candidate_trait": "leaf pigmentation",
            "wet_lab_activity": False,
            "gene_editing_activity": False,
            "approval_sequence": ["Source provenance review", "Candidate relevance review", "Interpretation approval", "Export and archive"],
        },
        "primary_outcome": "Traceable sequence-to-phenotype evidence map",
        "secondary_outcomes": ["Accession provenance", "Sequence checksum", "Sequence length", "GC percentage for nucleotide records", "Experiment linkage"],
        "sample_plan": {"records": "Up to 10 search results per query", "minimum_linked_records": 1, "evidence": ["NCBI accession", "FASTA", "metadata", "human interpretation"]},
        "approval_state": "draft",
        "evidence_mode": "public_reference",
        "limitations": "Computational evidence-management demonstration only. Imported public records do not prove trait causality, create a new variety, or authorize gene editing.",
    },
)


class BioinformaticsError(RuntimeError):
    pass


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_fasta(text: str) -> tuple[str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines or not lines[0].startswith(">"):
        raise BioinformaticsError("The provider did not return valid FASTA data.")
    header = lines[0][1:].strip()
    sequence = "".join(lines[1:]).replace(" ", "").upper()
    if not sequence:
        raise BioinformaticsError("The FASTA record did not contain a sequence.")
    return header, sequence


def sequence_metrics(database_name: str, sequence: str) -> dict[str, Any]:
    cleaned = sequence.upper().replace("-", "")
    if database_name == "nuccore":
        invalid = sorted(set(cleaned) - NUCLEOTIDE_ALPHABET)
        if invalid:
            raise BioinformaticsError("Unsupported nucleotide characters: " + ", ".join(invalid[:10]))
        gc_count = cleaned.count("G") + cleaned.count("C")
        ambiguity_count = sum(1 for base in cleaned if base not in {"A", "C", "G", "T", "U"})
        return {
            "sequence_type": "rna" if "U" in cleaned and "T" not in cleaned else "dna",
            "length": len(cleaned),
            "gc_percent": round((gc_count / len(cleaned)) * 100, 3),
            "ambiguity_count": ambiguity_count,
            "composition": dict(sorted(Counter(cleaned).items())),
        }
    invalid = sorted(set(cleaned) - PROTEIN_ALPHABET)
    if invalid:
        raise BioinformaticsError("Unsupported protein characters: " + ", ".join(invalid[:10]))
    return {
        "sequence_type": "protein",
        "length": len(cleaned),
        "gc_percent": None,
        "ambiguity_count": sum(1 for residue in cleaned if residue in {"B", "J", "O", "U", "X", "Z"}),
        "composition": dict(Counter(cleaned).most_common()),
    }


def _safe_database(value: str) -> str:
    result = value.strip().lower()
    if result not in ALLOWED_DATABASES:
        raise BioinformaticsError("Database must be nuccore or protein.")
    return result


def _safe_accession(value: str) -> str:
    result = value.strip()
    if not ACCESSION_RE.fullmatch(result):
        raise BioinformaticsError("Accession format is invalid.")
    return result


def _profile_email(conn: Any, user_id: str) -> str:
    configured = os.environ.get("AGROQ_NCBI_EMAIL", "").strip()
    if configured:
        return configured
    try:
        row = conn.execute("SELECT email FROM user_profiles WHERE user_id=?", (user_id,)).fetchone()
    except Exception:
        row = None
    if row and row["email"]:
        return str(row["email"])
    return "reyesothon1921@gmail.com"


def _rate_limit() -> None:
    global _LAST_REQUEST_AT
    minimum_interval = 0.34 if not os.environ.get("NCBI_API_KEY", "").strip() else 0.11
    with _RATE_LOCK:
        elapsed = time.monotonic() - _LAST_REQUEST_AT
        if elapsed < minimum_interval:
            time.sleep(minimum_interval - elapsed)
        _LAST_REQUEST_AT = time.monotonic()


def _ncbi_request(endpoint: str, params: dict[str, Any], *, email: str, expect_json: bool) -> Any:
    query = dict(params)
    query["tool"] = "AgroQSequencePortal"
    query["email"] = email
    api_key = os.environ.get("NCBI_API_KEY", "").strip()
    if api_key:
        query["api_key"] = api_key
    url = f"{NCBI_EUTILS}/{endpoint}?{urlencode(query)}"
    _rate_limit()
    req = Request(url, headers={"Accept": "application/json" if expect_json else "text/plain", "User-Agent": f"AgroQSequencePortal/1.0 ({email})"})
    try:
        with urlopen(req, timeout=20) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        raise BioinformaticsError(f"NCBI returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError) as exc:
        raise BioinformaticsError("NCBI could not be reached. Check the internet connection and retry.") from exc
    if not expect_json:
        return body
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise BioinformaticsError("NCBI returned unreadable JSON.") from exc


def ncbi_search(database_name: str, query_text: str, *, email: str) -> list[dict[str, Any]]:
    database_name = _safe_database(database_name)
    query_text = query_text.strip()
    if not query_text:
        raise BioinformaticsError("Enter a gene, protein, organism, or accession.")
    if len(query_text) > 300:
        raise BioinformaticsError("Search query is too long.")
    search = _ncbi_request("esearch.fcgi", {"db": database_name, "term": query_text, "retmode": "json", "retmax": 10, "sort": "relevance"}, email=email, expect_json=True)
    ids = search.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []
    summary = _ncbi_request("esummary.fcgi", {"db": database_name, "id": ",".join(ids), "retmode": "json"}, email=email, expect_json=True)
    result = summary.get("result", {})
    records: list[dict[str, Any]] = []
    for uid in result.get("uids", ids):
        item = result.get(str(uid), {})
        accession = item.get("accessionversion") or item.get("caption") or item.get("extra") or str(uid)
        length = item.get("slen") or item.get("length")
        records.append({
            "uid": str(uid),
            "database_name": database_name,
            "accession": str(accession),
            "title": str(item.get("title") or item.get("caption") or "Untitled sequence record"),
            "organism": str(item.get("organism") or ""),
            "length": int(length) if str(length or "").isdigit() else None,
        })
    return records


def ncbi_fetch(database_name: str, accession: str, *, email: str) -> dict[str, Any]:
    database_name = _safe_database(database_name)
    accession = _safe_accession(accession)
    fasta = _ncbi_request("efetch.fcgi", {"db": database_name, "id": accession, "rettype": "fasta", "retmode": "text"}, email=email, expect_json=False)
    header, sequence = parse_fasta(fasta)
    metrics = sequence_metrics(database_name, sequence)
    organism_match = re.search(r"\[([^\[\]]+)\]\s*$", header)
    return {
        "database_name": database_name,
        "accession": accession,
        "title": header,
        "organism": organism_match.group(1) if organism_match else "",
        "fasta_header": header,
        "sequence": sequence,
        "metrics": metrics,
        "source_url": f"https://www.ncbi.nlm.nih.gov/{'nuccore' if database_name == 'nuccore' else 'protein'}/{accession}",
    }


def _table_exists(conn: Any, table_name: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone() is not None


def _count_table(conn: Any, table_name: str) -> int:
    allow = {"users", "access_requests", "invite_codes", "beta_reservations", "experiments", "observations", "manual_tasks", "recommendations", "biological_sequences", "experiment_sequence_links", "audit_events", "gateway_devices", "backup_runs"}
    if table_name not in allow or not _table_exists(conn, table_name):
        return 0
    return int(conn.execute(f"SELECT COUNT(*) AS n FROM {table_name}").fetchone()["n"])


def register_bioinformatics_portal(*, app: Any, get_db: Callable[..., Any], record_audit_event: Callable[..., Any], roles_required: Callable[..., Any]) -> None:
    bp = Blueprint("agroq_bio", __name__)
    initialized = False
    init_lock = threading.Lock()

    def ensure_schema() -> None:
        nonlocal initialized
        if initialized:
            return
        with init_lock:
            if initialized:
                return
            sql = (BASE_DIR / "bioinformatics_schema.sql").read_text(encoding="utf-8")
            with get_db() as conn:
                conn.executescript(sql)
                seed_demo_experiments(conn)
            initialized = True

    def seed_demo_experiments(conn: Any) -> None:
        now = utc_timestamp()
        admin = conn.execute("SELECT user_id FROM users WHERE role='administrator' AND active=1 ORDER BY created_at LIMIT 1").fetchone()
        if admin is None:
            return
        admin_id = admin["user_id"]
        for spec in DEMO_EXPERIMENTS:
            conn.execute("""INSERT OR IGNORE INTO experiments(experiment_id,title,hypothesis,status,plot_id,owner,created_at) VALUES(?,?,?,?,?,?,?)""", (spec["experiment_id"], spec["title"], spec["hypothesis"], spec["status"], spec["plot_id"], spec["owner"], now))
            conn.execute("""INSERT INTO bio_experiment_specs(experiment_id,demo_class,organism,cultivar,objective,design_json,primary_outcome,secondary_outcomes_json,sample_plan_json,approval_state,evidence_mode,limitations,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(experiment_id) DO UPDATE SET demo_class=excluded.demo_class,organism=excluded.organism,cultivar=excluded.cultivar,objective=excluded.objective,design_json=excluded.design_json,primary_outcome=excluded.primary_outcome,secondary_outcomes_json=excluded.secondary_outcomes_json,sample_plan_json=excluded.sample_plan_json,approval_state=excluded.approval_state,evidence_mode=excluded.evidence_mode,limitations=excluded.limitations,updated_at=excluded.updated_at""", (spec["experiment_id"], spec["demo_class"], spec["organism"], spec["cultivar"], spec["objective"], json.dumps(spec["design"], separators=(",", ":")), spec["primary_outcome"], json.dumps(spec["secondary_outcomes"], separators=(",", ":")), json.dumps(spec["sample_plan"], separators=(",", ":")), spec["approval_state"], spec["evidence_mode"], spec["limitations"], now, now))
        treatments = (
            ("AGQ-TRT-001-LW", "AGQ-PHENO-001", "70% irrigation treatment", "Synthetic low-water treatment.", 0),
            ("AGQ-TRT-001-CTRL", "AGQ-PHENO-001", "100% irrigation control", "Synthetic full-irrigation control.", 1),
            ("AGQ-TRT-002-WARM", "AGQ-PHENO-002", "Warm-condition treatment", "Synthetic warm-condition scenario.", 0),
            ("AGQ-TRT-002-CTRL", "AGQ-PHENO-002", "Baseline control", "Synthetic baseline scenario.", 1),
        )
        for row in treatments:
            conn.execute("""INSERT OR IGNORE INTO treatments(treatment_id,experiment_id,name,description,is_control,created_by,created_at) VALUES(?,?,?,?,?,?,?)""", (*row, admin_id, now))
        assignments = (
            ("AGQ-ASN-001-LW", "AGQ-PHENO-001", "AGQ-TRT-001-LW", "AGQ-PLOT-002", "Synthetic group of six plants."),
            ("AGQ-ASN-001-CTRL", "AGQ-PHENO-001", "AGQ-TRT-001-CTRL", "AGQ-PLOT-001", "Synthetic control group of six plants."),
            ("AGQ-ASN-002-WARM", "AGQ-PHENO-002", "AGQ-TRT-002-WARM", "AGQ-PLOT-003", "Synthetic warm-condition group of six plants."),
            ("AGQ-ASN-002-CTRL", "AGQ-PHENO-002", "AGQ-TRT-002-CTRL", "AGQ-PLOT-001", "Synthetic baseline group of six plants."),
        )
        for assignment_id, experiment_id, treatment_id, plot_id, notes in assignments:
            if conn.execute("SELECT 1 FROM plots WHERE plot_id=?", (plot_id,)).fetchone():
                conn.execute("""INSERT OR IGNORE INTO treatment_assignments(assignment_id,experiment_id,treatment_id,plot_id,responsible_user_id,assigned_at,notes) VALUES(?,?,?,?,?,?,?)""", (assignment_id, experiment_id, treatment_id, plot_id, admin_id, now, notes))
        approvals = (
            ("AGQ-BIOAPP-001", "AGQ-PHENO-001", "Synthetic demo protocol", "approved", "Approved for software demonstration only.", admin_id),
            ("AGQ-BIOAPP-002", "AGQ-PHENO-002", "Protocol review", "pending", "Awaiting administrator review before activation.", None),
            ("AGQ-BIOAPP-003", "AGQ-GENO-003", "Source provenance review", "pending", "Public records must preserve accession and source.", None),
        )
        for row in approvals:
            conn.execute("""INSERT OR IGNORE INTO bio_experiment_approval_events(approval_event_id,experiment_id,gate_name,decision,rationale,reviewer_id,reviewed_at) VALUES(?,?,?,?,?,?,?)""", (*row, now))

    @bp.before_request
    def _ensure() -> None:
        ensure_schema()

    @bp.get("/admin/control-center")
    @roles_required("administrator")
    def control_center_page() -> Any:
        with get_db() as conn:
            counts = {table: _count_table(conn, table) for table in ("users", "access_requests", "invite_codes", "beta_reservations", "experiments", "observations", "manual_tasks", "recommendations", "biological_sequences", "audit_events")}
        return render_template("admin_control_center.html", counts=counts, current_user=g.user)

    @bp.get("/bioinformatics")
    @roles_required("administrator", "researcher")
    def bioinformatics_page() -> Any:
        return render_template("bioinformatics_portal.html")

    @bp.get("/api/bio/session")
    @roles_required("administrator", "researcher")
    def bio_session() -> Any:
        token = session.get("bio_csrf_token")
        if not token:
            token = secrets.token_urlsafe(32)
            session["bio_csrf_token"] = token
        with get_db() as conn:
            email = _profile_email(conn, g.user["user_id"])
        return jsonify({"ok": True, "role": g.user["role"], "user_id": g.user["user_id"], "display_name": g.user["display_name"], "contact_email": email, "csrf_token": token, "field_mode": "locked", "evidence_mode": "synthetic_manual_public_reference"})

    @bp.get("/api/admin/overview")
    @roles_required("administrator")
    def admin_overview() -> Any:
        with get_db() as conn:
            counts = {table: _count_table(conn, table) for table in ("users", "access_requests", "invite_codes", "beta_reservations", "experiments", "observations", "manual_tasks", "recommendations", "biological_sequences", "experiment_sequence_links", "audit_events", "gateway_devices", "backup_runs")}
            recent_audit = [dict(row) for row in conn.execute("SELECT action,entity_type,entity_id,created_at FROM audit_events ORDER BY created_at DESC LIMIT 10").fetchall()]
        return jsonify({"ok": True, "admin": {"user_id": g.user["user_id"], "display_name": g.user["display_name"], "role": g.user["role"]}, "counts": counts, "recent_audit": recent_audit, "field_mode": "locked", "physical_actions_enabled": False})

    @bp.get("/api/bio/experiments")
    @roles_required("administrator", "researcher", "viewer")
    def bio_experiments() -> Any:
        with get_db() as conn:
            rows = conn.execute("""SELECT e.experiment_id,e.title,e.hypothesis,e.status,e.plot_id,e.owner,s.demo_class,s.organism,s.cultivar,s.objective,s.design_json,s.primary_outcome,s.secondary_outcomes_json,s.sample_plan_json,s.approval_state,s.evidence_mode,s.limitations,(SELECT COUNT(*) FROM experiment_sequence_links l WHERE l.experiment_id=e.experiment_id) AS sequence_count FROM experiments e JOIN bio_experiment_specs s ON s.experiment_id=e.experiment_id ORDER BY e.experiment_id""").fetchall()
        items = []
        for row in rows:
            item = dict(row)
            item["design"] = json.loads(item.pop("design_json"))
            item["secondary_outcomes"] = json.loads(item.pop("secondary_outcomes_json"))
            item["sample_plan"] = json.loads(item.pop("sample_plan_json"))
            items.append(item)
        return jsonify({"ok": True, "experiments": items})

    @bp.post("/api/bio/experiments/<experiment_id>/approval")
    @roles_required("administrator")
    def approve_experiment(experiment_id: str) -> Any:
        token = request.headers.get("X-CSRF-Token", "")
        expected = session.get("bio_csrf_token", "")
        if not expected or not secrets.compare_digest(token, expected):
            return jsonify({"ok": False, "error": "Invalid CSRF token."}), 403
        payload = request.get_json(silent=True) or {}
        decision = str(payload.get("decision", "")).strip()
        rationale = str(payload.get("rationale", "")).strip()
        if decision not in {"approved", "rejected", "pending"} or not rationale:
            return jsonify({"ok": False, "error": "A valid decision and rationale are required."}), 400
        state = {"approved": "approved_for_demo", "rejected": "rejected", "pending": "pending_review"}[decision]
        with get_db() as conn:
            if not conn.execute("SELECT 1 FROM bio_experiment_specs WHERE experiment_id=?", (experiment_id,)).fetchone():
                return jsonify({"ok": False, "error": "Experiment not found."}), 404
            conn.execute("UPDATE bio_experiment_specs SET approval_state=?,updated_at=? WHERE experiment_id=?", (state, utc_timestamp(), experiment_id))
            conn.execute("""INSERT INTO bio_experiment_approval_events(approval_event_id,experiment_id,gate_name,decision,rationale,reviewer_id,reviewed_at) VALUES(?,?,?,?,?,?,?)""", (f"AGQ-BIOAPP-{time.time_ns()}", experiment_id, "Administrator demonstration gate", decision, rationale[:2000], g.user["user_id"], utc_timestamp()))
        record_audit_event(g.user["user_id"], "bio_experiment_approval", "experiment", experiment_id, json.dumps({"decision": decision, "rationale": rationale[:500]}))
        return jsonify({"ok": True, "approval_state": state})

    @bp.get("/api/bio/search")
    @roles_required("administrator", "researcher")
    def bio_search() -> Any:
        database_name = request.args.get("database", "nuccore")
        query_text = request.args.get("q", "")
        try:
            with get_db() as conn:
                email = _profile_email(conn, g.user["user_id"])
            records = ncbi_search(database_name, query_text, email=email)
            with get_db() as conn:
                conn.execute("""INSERT INTO sequence_lookup_audit(lookup_id,database_name,query_text,result_count,status,requested_by,requested_at,details) VALUES(?,?,?,?,?,?,?,?)""", (f"AGQ-LOOKUP-{time.time_ns()}", _safe_database(database_name), query_text.strip(), len(records), "success" if records else "no_results", g.user["user_id"], utc_timestamp(), None))
            return jsonify({"ok": True, "results": records})
        except BioinformaticsError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @bp.get("/api/bio/fetch")
    @roles_required("administrator", "researcher")
    def bio_fetch() -> Any:
        try:
            with get_db() as conn:
                email = _profile_email(conn, g.user["user_id"])
            record = ncbi_fetch(request.args.get("database", "nuccore"), request.args.get("accession", ""), email=email)
            preview = dict(record)
            preview["sequence_preview"] = record["sequence"][:240]
            preview["sequence_truncated"] = len(record["sequence"]) > 240
            preview.pop("sequence")
            return jsonify({"ok": True, "record": preview})
        except BioinformaticsError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @bp.post("/api/bio/insert")
    @roles_required("administrator", "researcher")
    def bio_insert() -> Any:
        token = request.headers.get("X-CSRF-Token", "")
        expected = session.get("bio_csrf_token", "")
        if not expected or not secrets.compare_digest(token, expected):
            return jsonify({"ok": False, "error": "Invalid CSRF token."}), 403
        payload = request.get_json(silent=True) or {}
        database_name = str(payload.get("database_name", "nuccore"))
        accession = str(payload.get("accession", ""))
        experiment_id = str(payload.get("experiment_id", "")).strip()
        evidence_class = str(payload.get("evidence_class", "candidate")).strip()
        relationship_label = str(payload.get("relationship_label", "candidate public sequence evidence")).strip()[:120]
        interpretation = str(payload.get("interpretation", "")).strip()[:2000]
        if evidence_class not in {"reference", "candidate", "supporting", "control", "excluded"}:
            return jsonify({"ok": False, "error": "Evidence class is invalid."}), 400
        try:
            with get_db() as conn:
                email = _profile_email(conn, g.user["user_id"])
            record = ncbi_fetch(database_name, accession, email=email)
            sequence = record["sequence"]
            metrics = record["metrics"]
            digest = hashlib.sha256(sequence.encode("utf-8")).hexdigest()
            sequence_id = f"AGQ-SEQ-{digest[:20].upper()}"
            metadata = {"provider": "NCBI E-utilities", "retrieved_at": utc_timestamp(), "metrics": metrics, "disclaimer": "Public reference record. Association does not establish phenotype causality."}
            with get_db() as conn:
                conn.execute("""INSERT INTO biological_sequences(sequence_id,database_name,accession,sequence_type,title,organism,fasta_header,sequence_text,sequence_length,gc_percent,ambiguity_count,sha256,source_url,metadata_json,imported_by,imported_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(database_name,accession) DO UPDATE SET title=excluded.title,organism=excluded.organism,fasta_header=excluded.fasta_header,sequence_text=excluded.sequence_text,sequence_length=excluded.sequence_length,gc_percent=excluded.gc_percent,ambiguity_count=excluded.ambiguity_count,sha256=excluded.sha256,source_url=excluded.source_url,metadata_json=excluded.metadata_json""", (sequence_id, record["database_name"], record["accession"], metrics["sequence_type"], record["title"], record["organism"], record["fasta_header"], sequence, metrics["length"], metrics["gc_percent"], metrics["ambiguity_count"], digest, record["source_url"], json.dumps(metadata, separators=(",", ":")), g.user["user_id"], utc_timestamp()))
                sequence_id = conn.execute("SELECT sequence_id FROM biological_sequences WHERE database_name=? AND accession=?", (record["database_name"], record["accession"])).fetchone()["sequence_id"]
                if experiment_id:
                    if not conn.execute("SELECT 1 FROM experiments WHERE experiment_id=?", (experiment_id,)).fetchone():
                        raise BioinformaticsError("Selected experiment does not exist.")
                    conn.execute("""INSERT INTO experiment_sequence_links(link_id,experiment_id,sequence_id,relationship_label,evidence_class,interpretation,linked_by,linked_at) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(experiment_id,sequence_id,relationship_label) DO UPDATE SET evidence_class=excluded.evidence_class,interpretation=excluded.interpretation,linked_by=excluded.linked_by,linked_at=excluded.linked_at""", (f"AGQ-SEQLINK-{time.time_ns()}", experiment_id, sequence_id, relationship_label or "candidate public sequence evidence", evidence_class, interpretation or None, g.user["user_id"], utc_timestamp()))
            record_audit_event(g.user["user_id"], "sequence_imported", "biological_sequence", sequence_id, json.dumps({"database": record["database_name"], "accession": record["accession"], "experiment_id": experiment_id or None, "sha256": digest}))
            return jsonify({"ok": True, "sequence_id": sequence_id, "accession": record["accession"], "experiment_id": experiment_id or None})
        except BioinformaticsError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @bp.get("/api/bio/sequences")
    @roles_required("administrator", "researcher", "viewer")
    def bio_sequences() -> Any:
        with get_db() as conn:
            rows = conn.execute("""SELECT s.sequence_id,s.database_name,s.accession,s.sequence_type,s.title,s.organism,s.sequence_length,s.gc_percent,s.ambiguity_count,s.sha256,s.source_url,s.imported_at,GROUP_CONCAT(DISTINCT l.experiment_id) AS experiment_ids FROM biological_sequences s LEFT JOIN experiment_sequence_links l ON l.sequence_id=s.sequence_id GROUP BY s.sequence_id ORDER BY s.imported_at DESC""").fetchall()
        items = []
        for row in rows:
            item = dict(row)
            item["experiment_ids"] = item["experiment_ids"].split(",") if item["experiment_ids"] else []
            items.append(item)
        return jsonify({"ok": True, "sequences": items})

    @bp.get("/api/bio/sequences/<sequence_id>/export")
    @roles_required("administrator", "researcher", "viewer")
    def bio_export(sequence_id: str) -> Any:
        export_format = request.args.get("format", "fasta").lower()
        if export_format not in ALLOWED_EXPORTS:
            return jsonify({"ok": False, "error": "Unsupported export format."}), 400
        with get_db() as conn:
            row = conn.execute("SELECT * FROM biological_sequences WHERE sequence_id=?", (sequence_id,)).fetchone()
            links = conn.execute("SELECT experiment_id,relationship_label,evidence_class,interpretation,linked_at FROM experiment_sequence_links WHERE sequence_id=? ORDER BY linked_at", (sequence_id,)).fetchall()
        if row is None:
            return jsonify({"ok": False, "error": "Sequence not found."}), 404
        item = dict(row)
        item["metadata"] = json.loads(item.pop("metadata_json"))
        item["experiment_links"] = [dict(link) for link in links]
        safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", item["accession"])
        if export_format == "fasta":
            wrapped = "\n".join(item["sequence_text"][i:i + 80] for i in range(0, len(item["sequence_text"]), 80))
            return Response(f">{item['fasta_header']}\n{wrapped}\n", mimetype="text/plain", headers={"Content-Disposition": f'attachment; filename="{safe_name}.fasta"'})
        if export_format == "json":
            return Response(json.dumps(item, indent=2), mimetype="application/json", headers={"Content-Disposition": f'attachment; filename="{safe_name}.json"'})
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["sequence_id", "database_name", "accession", "sequence_type", "title", "organism", "sequence_length", "gc_percent", "ambiguity_count", "sha256", "source_url", "experiment_ids"])
        writer.writerow([item["sequence_id"], item["database_name"], item["accession"], item["sequence_type"], item["title"], item["organism"], item["sequence_length"], item["gc_percent"], item["ambiguity_count"], item["sha256"], item["source_url"], "|".join(link["experiment_id"] for link in item["experiment_links"])])
        return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f'attachment; filename="{safe_name}.csv"'})

    app.register_blueprint(bp)
