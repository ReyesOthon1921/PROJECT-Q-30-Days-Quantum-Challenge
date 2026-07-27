CREATE TABLE IF NOT EXISTS research_model_reviews (
 id INTEGER PRIMARY KEY AUTOINCREMENT, model_version TEXT NOT NULL, dataset_version TEXT NOT NULL,
 reviewer TEXT NOT NULL, decision TEXT NOT NULL CHECK(decision IN ('approve','reject','request_more_evidence')),
 rationale TEXT NOT NULL, created_at TEXT NOT NULL, immutable INTEGER NOT NULL DEFAULT 1 CHECK(immutable=1));
CREATE TRIGGER IF NOT EXISTS research_model_reviews_no_update BEFORE UPDATE ON research_model_reviews
BEGIN SELECT RAISE(ABORT,'research review history is immutable'); END;
CREATE TRIGGER IF NOT EXISTS research_model_reviews_no_delete BEFORE DELETE ON research_model_reviews
BEGIN SELECT RAISE(ABORT,'research review history is immutable'); END;
