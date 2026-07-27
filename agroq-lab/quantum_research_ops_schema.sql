-- AgroQ Q15 research operations, lifecycle, evidence, and release schema.

CREATE TABLE IF NOT EXISTS quantum_research_operations (
    operation_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    run_id TEXT UNIQUE,
    lifecycle_state TEXT NOT NULL CHECK(lifecycle_state IN (
        'Draft','Registered','Dataset attached','Ready to run',
        'Running','Completed','Failed','Under review',
        'Approved for research','Rejected','Superseded','Released'
    )),
    researcher_id TEXT NOT NULL,
    reviewer_id TEXT,
    supersedes_operation_id TEXT,
    superseded_by_operation_id TEXT,
    research_notes TEXT NOT NULL DEFAULT '',
    limitations TEXT NOT NULL DEFAULT '',
    release_checklist_json TEXT NOT NULL,
    released_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(experiment_id)
        REFERENCES quantum_experiments(experiment_id) ON DELETE CASCADE,
    FOREIGN KEY(run_id)
        REFERENCES quantum_runs(run_id) ON DELETE SET NULL,
    FOREIGN KEY(researcher_id) REFERENCES users(user_id),
    FOREIGN KEY(reviewer_id) REFERENCES users(user_id),
    FOREIGN KEY(supersedes_operation_id)
        REFERENCES quantum_research_operations(operation_id),
    FOREIGN KEY(superseded_by_operation_id)
        REFERENCES quantum_research_operations(operation_id),
    CHECK(reviewer_id IS NULL OR reviewer_id <> researcher_id)
);

CREATE INDEX IF NOT EXISTS idx_quantum_ops_state
ON quantum_research_operations(lifecycle_state, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_quantum_ops_experiment
ON quantum_research_operations(experiment_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_quantum_ops_researcher
ON quantum_research_operations(researcher_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS quantum_lifecycle_events (
    event_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL,
    run_id TEXT,
    from_state TEXT,
    to_state TEXT NOT NULL,
    reason TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(operation_id)
        REFERENCES quantum_research_operations(operation_id) ON DELETE CASCADE,
    FOREIGN KEY(run_id) REFERENCES quantum_runs(run_id) ON DELETE SET NULL,
    FOREIGN KEY(actor_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_quantum_lifecycle_operation
ON quantum_lifecycle_events(operation_id, created_at);

CREATE INDEX IF NOT EXISTS idx_quantum_lifecycle_run
ON quantum_lifecycle_events(run_id, created_at);

CREATE TABLE IF NOT EXISTS quantum_release_checklist_events (
    checklist_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL,
    run_id TEXT,
    checklist_json TEXT NOT NULL,
    complete INTEGER NOT NULL CHECK(complete IN (0,1)),
    evaluated_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(operation_id)
        REFERENCES quantum_research_operations(operation_id) ON DELETE CASCADE,
    FOREIGN KEY(run_id) REFERENCES quantum_runs(run_id) ON DELETE SET NULL,
    FOREIGN KEY(evaluated_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_quantum_checklist_operation
ON quantum_release_checklist_events(operation_id, created_at DESC);

CREATE TABLE IF NOT EXISTS quantum_evidence_bundles (
    bundle_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    bundle_sha256 TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(operation_id)
        REFERENCES quantum_research_operations(operation_id) ON DELETE CASCADE,
    FOREIGN KEY(run_id) REFERENCES quantum_runs(run_id) ON DELETE CASCADE,
    FOREIGN KEY(created_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_quantum_bundle_operation
ON quantum_evidence_bundles(operation_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_quantum_bundle_run
ON quantum_evidence_bundles(run_id, created_at DESC);

CREATE TRIGGER IF NOT EXISTS trg_quantum_lifecycle_no_update
BEFORE UPDATE ON quantum_lifecycle_events
BEGIN
    SELECT RAISE(ABORT, 'Quantum lifecycle history is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_quantum_lifecycle_no_delete
BEFORE DELETE ON quantum_lifecycle_events
BEGIN
    SELECT RAISE(ABORT, 'Quantum lifecycle history is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_quantum_bundle_no_update
BEFORE UPDATE ON quantum_evidence_bundles
BEGIN
    SELECT RAISE(ABORT, 'Quantum evidence bundle records are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_quantum_bundle_no_delete
BEFORE DELETE ON quantum_evidence_bundles
BEGIN
    SELECT RAISE(ABORT, 'Quantum evidence bundle records are immutable.');
END;
