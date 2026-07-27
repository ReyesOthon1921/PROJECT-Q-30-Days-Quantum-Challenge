import pytest
import app as app_module
from app import app, get_db, init_db

@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module,"DB_PATH",tmp_path/"research_translation.db")
    app.config.update(TESTING=True,SECRET_KEY="research-translation-test")
    init_db()
    return app.test_client()

def test_searchable_sources_api(client):
    r=client.get("/api/research-translation/sources?q=FAIR&sequence=Q29")
    assert r.status_code==200 and r.get_json()["count"]==1

def test_viewer_cannot_create_review(client):
    with client.session_transaction() as s: s["role"]="viewer"
    assert client.post("/api/research-translation/reviews",json={"decision":"approve"}).status_code==403

def test_researcher_can_record_bounded_review(client):
    with client.session_transaction() as s:
        s["role"]="researcher"; s["reviewer_label"]="Q26 test researcher"
    r=client.post("/api/research-translation/reviews",json={"decision":"request_more_evidence",
      "rationale":"More bounded synthetic evidence is required."})
    assert r.status_code==201 and r.get_json()["automatic_field_instruction"] is False
    with get_db() as conn:
        row=conn.execute("SELECT * FROM research_model_reviews WHERE id=?",(r.get_json()["review_id"],)).fetchone()
    assert row is not None and row["decision"]=="request_more_evidence" and row["immutable"]==1
