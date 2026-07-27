import io, sqlite3, zipfile
from pathlib import Path
import pytest
from research_translation import benchmark, build_evidence_zip, deterministic_twin, model_evaluation, publication_scaffold
def test_digital_twin_is_synthetic_and_locked():
    d=deterministic_twin(); assert d["synthetic"] and not d["real_time"] and d["field_mode"]=="locked"
def test_model_requires_human_control():
    assert model_evaluation()["automatic_field_instruction"] is False
def test_benchmark_has_matched_classical_baseline():
    b=benchmark(); assert b["matched_budget"] and b["classical"] and not b["uav_operation"]
def test_publication_and_authorship_are_not_automatic():
    p=publication_scaffold(); assert not p["paper_submitted"] and not p["authorship_automatic"]
def test_evidence_zip_is_deterministic_and_has_manifest():
    a=build_evidence_zip(); assert a==build_evidence_zip()
    with zipfile.ZipFile(io.BytesIO(a)) as z: assert "SHA256SUMS.txt" in z.namelist()
def test_review_schema_is_immutable():
    db=sqlite3.connect(":memory:")
    db.executescript((Path(__file__).resolve().parents[1]/"research_translation_schema.sql").read_text())
    db.execute("INSERT INTO research_model_reviews(model_version,dataset_version,reviewer,decision,rationale,created_at) VALUES(?,?,?,?,?,?)",
      ("model-v1","data-v1","reviewer","approve","bounded synthetic review","2026-07-27T00:00:00Z"))
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("UPDATE research_model_reviews SET decision='reject' WHERE id=1")
