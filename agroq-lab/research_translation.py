from __future__ import annotations
import hashlib, io, json, sqlite3, zipfile
from datetime import datetime, timezone
from pathlib import Path
from flask import g, jsonify, request, session

BASE_DIR = Path(__file__).resolve().parent
REGISTRY_PATH = BASE_DIR / "research_translation_registry.json"
SCHEMA_PATH = BASE_DIR / "research_translation_schema.sql"
SEED = 26030

def load_registry():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

def deterministic_twin():
    return {"dataset_version":"agroq-synthetic-twin-v1","seed":SEED,"synthetic":True,"real_time":False,
      "field_mode":"locked","plots":[{"id":"P-01","zone":"North Control","moisture":23,"uncertainty":0.08}],
      "lineage":["manual-observation","synthetic-sensor","model-v1","human-review"],"human_verified":False}

def model_evaluation():
    return {"dataset":"agroq-xai-synthetic-v1","frozen":True,"seed":SEED,"train_rows":24,"test_rows":8,
      "baseline":{"name":"mean predictor","mae":0.182},"candidate":{"name":"deterministic linear model","mae":0.137},
      "feature_contributions":{"soil_moisture":0.42,"temperature":0.21,"treatment":0.14},
      "confidence":0.71,"uncertainty":0.12,"automatic_field_instruction":False}

def benchmark():
    return {"id":"agroq-placement-v1","seed":SEED,"synthetic":True,"field_mode":"locked",
      "classical":{"method":"greedy","score":18.0},"qubo":{"registered":True,"simulator_score":18.5},
      "matched_budget":True,"uav_operation":False,"sensor_installation":False}

def publication_scaffold():
    return {"title":"Design and Evaluation of a Local-First, Evidence-Traceable Digital-Acre Platform for Human-Supervised Agricultural Research",
      "status":"scaffold; awaiting real evidence","paper_submitted":False,"authorship_automatic":False,
      "contributors":[{"name":"Othon Reyes Jr.","role":"Founder and Research Lead"},
      {"name":"Edith Ortiz","role":"Co-Founder and Operations Lead"},
      {"name":"Misbahul Islam","role":"Research Mentor & Publication Collaborator"}],
      "authorship_boundary":"Authorship requires documented publication contributions.",
      "sections":["Abstract","Research problem","Research questions","Hypotheses","Related work","Architecture",
      "Experimental design","Classical baselines","Reproduction procedure","Acceptance criteria","Results",
      "Limitations","Ethics and AI-use disclosure","Synthetic-data disclosure","Quantum-claim boundary","Future work"]}

def build_evidence_zip():
    records={"digital_twin.json":deterministic_twin(),"model_evaluation.json":model_evaluation(),
      "benchmark.json":benchmark(),"publication.json":publication_scaffold(),"registry.json":load_registry()}
    payload={k:(json.dumps(v,sort_keys=True,indent=2)+"\n").encode() for k,v in records.items()}
    sums="\n".join(f"{hashlib.sha256(payload[k]).hexdigest()}  {k}" for k in sorted(payload))+"\n"
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        for name in sorted(payload):
            info=zipfile.ZipInfo(name,(2026,1,1,0,0,0)); info.external_attr=0o644<<16
            z.writestr(info,payload[name])
        info=zipfile.ZipInfo("SHA256SUMS.txt",(2026,1,1,0,0,0)); info.external_attr=0o644<<16
        z.writestr(info,sums.encode())
    return out.getvalue()

def _review_identity():
    user=getattr(g,"user",None)
    if user:
        return user.get("role","viewer"), user.get("user_id"), user.get("display_name") or user.get("username")
    role=session.get("role","viewer")
    return role, None, session.get("reviewer_label") or role

def _ensure_review_schema(get_db):
    if get_db is None: raise RuntimeError("research review database is unavailable")
    with get_db() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

def register_research_translation(app, get_db=None, roles_required=None, record_audit_event=None):
    @app.get("/api/research-translation/sources")
    def research_sources():
        q=request.args.get("q","").strip().lower()
        sequence=request.args.get("sequence","").strip().upper()
        sources=load_registry()["sources"]
        if q: sources=[s for s in sources if q in json.dumps(s).lower()]
        if sequence: sources=[s for s in sources if sequence in s["sequence"]]
        return jsonify({"sources":sources,"count":len(sources),"version":load_registry()["version"]})
    @app.get("/api/research-translation/digital-twin")
    def research_twin(): return jsonify(deterministic_twin())
    @app.get("/api/research-translation/model-evaluation")
    def research_model(): return jsonify(model_evaluation())
    @app.get("/api/research-translation/benchmark")
    def research_benchmark(): return jsonify(benchmark())
    @app.get("/api/research-translation/publication")
    def research_publication(): return jsonify(publication_scaffold())
    @app.post("/api/research-translation/reviews")
    def add_review():
        role,reviewer_id,reviewer_label=_review_identity()
        if role not in {"administrator","researcher"}: return jsonify({"error":"forbidden"}),403
        body=request.get_json(silent=True) or {}
        decision=str(body.get("decision","")).strip()
        if decision not in {"approve","reject","request_more_evidence"}: return jsonify({"error":"invalid decision"}),400
        model_version=str(body.get("model_version","model-v1")).strip() or "model-v1"
        dataset_version=str(body.get("dataset_version","agroq-xai-synthetic-v1")).strip() or "agroq-xai-synthetic-v1"
        rationale=str(body.get("rationale","Bounded synthetic research review.")).strip()
        if not rationale: return jsonify({"error":"rationale is required"}),400
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds")
        _ensure_review_schema(get_db)
        with get_db() as conn:
            cursor=conn.execute("""INSERT INTO research_model_reviews(
              model_version,dataset_version,reviewer,decision,rationale,created_at
            ) VALUES(?,?,?,?,?,?)""",(model_version,dataset_version,reviewer_label,decision,rationale,created_at))
            review_id=cursor.lastrowid
        if record_audit_event is not None:
            record_audit_event(reviewer_id,"research_model_review_recorded","research_model_review",str(review_id),
              json.dumps({"decision":decision,"model_version":model_version,"dataset_version":dataset_version}))
        return jsonify({"review_id":review_id,"decision":decision,"immutable":True,
          "automatic_field_instruction":False,"created_at":created_at}),201
