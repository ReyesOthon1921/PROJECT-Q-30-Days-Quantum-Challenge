CREATE TABLE IF NOT EXISTS biological_sequences (
    sequence_id TEXT PRIMARY KEY,
    database_name TEXT NOT NULL CHECK(database_name IN ('nuccore','protein')),
    accession TEXT NOT NULL,
    sequence_type TEXT NOT NULL CHECK(sequence_type IN ('dna','rna','protein')),
    title TEXT NOT NULL,
    organism TEXT,
    fasta_header TEXT NOT NULL,
    sequence_text TEXT NOT NULL,
    sequence_length INTEGER NOT NULL,
    gc_percent REAL,
    ambiguity_count INTEGER NOT NULL DEFAULT 0,
    sha256 TEXT NOT NULL,
    source_url TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    imported_by TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    UNIQUE(database_name, accession),
    FOREIGN KEY(imported_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS experiment_sequence_links (
    link_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    sequence_id TEXT NOT NULL,
    relationship_label TEXT NOT NULL,
    evidence_class TEXT NOT NULL CHECK(evidence_class IN ('reference','candidate','supporting','control','excluded')),
    interpretation TEXT,
    linked_by TEXT NOT NULL,
    linked_at TEXT NOT NULL,
    UNIQUE(experiment_id, sequence_id, relationship_label),
    FOREIGN KEY(experiment_id) REFERENCES experiments(experiment_id),
    FOREIGN KEY(sequence_id) REFERENCES biological_sequences(sequence_id),
    FOREIGN KEY(linked_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS bio_experiment_specs (
    experiment_id TEXT PRIMARY KEY,
    demo_class TEXT NOT NULL CHECK(demo_class IN ('phenotype','genotype_to_phenotype','sequence_evidence')),
    organism TEXT NOT NULL,
    cultivar TEXT,
    objective TEXT NOT NULL,
    design_json TEXT NOT NULL,
    primary_outcome TEXT NOT NULL,
    secondary_outcomes_json TEXT NOT NULL,
    sample_plan_json TEXT NOT NULL,
    approval_state TEXT NOT NULL CHECK(approval_state IN ('draft','pending_review','approved_for_demo','rejected','completed')),
    evidence_mode TEXT NOT NULL CHECK(evidence_mode IN ('synthetic','manual','public_reference','mixed')),
    limitations TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(experiment_id) REFERENCES experiments(experiment_id)
);

CREATE TABLE IF NOT EXISTS bio_experiment_approval_events (
    approval_event_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    gate_name TEXT NOT NULL,
    decision TEXT NOT NULL CHECK(decision IN ('approved','rejected','pending')),
    rationale TEXT NOT NULL,
    reviewer_id TEXT,
    reviewed_at TEXT NOT NULL,
    FOREIGN KEY(experiment_id) REFERENCES experiments(experiment_id),
    FOREIGN KEY(reviewer_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS sequence_lookup_audit (
    lookup_id TEXT PRIMARY KEY,
    database_name TEXT NOT NULL CHECK(database_name IN ('nuccore','protein')),
    query_text TEXT NOT NULL,
    result_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL CHECK(status IN ('success','no_results','error')),
    requested_by TEXT NOT NULL,
    requested_at TEXT NOT NULL,
    details TEXT,
    FOREIGN KEY(requested_by) REFERENCES users(user_id)
);
