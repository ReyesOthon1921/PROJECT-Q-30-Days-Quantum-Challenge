-- AgroQ Q17-Q19 controlled staging, beta operations, and evidence schema.

CREATE TABLE IF NOT EXISTS staging_candidates (
    candidate_id TEXT PRIMARY KEY,
    commit_sha TEXT NOT NULL,
    release_tag TEXT NOT NULL,
    backend_url TEXT,
    frontend_url TEXT,
    service_id TEXT,
    status TEXT NOT NULL CHECK(status IN (
        'draft','deployed','verifying','accepted','rejected','superseded'
    )),
    notes TEXT NOT NULL DEFAULT '',
    created_by TEXT NOT NULL,
    accepted_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    accepted_at TEXT,
    FOREIGN KEY(created_by) REFERENCES users(user_id),
    FOREIGN KEY(accepted_by) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_staging_candidates_commit_tag
ON staging_candidates(commit_sha, release_tag);

CREATE INDEX IF NOT EXISTS idx_staging_candidates_status
ON staging_candidates(status, updated_at DESC);

CREATE TABLE IF NOT EXISTS staging_acceptance_checks (
    check_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    check_code TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN (
        'backend','frontend','access','persistence','release','rollback'
    )),
    status TEXT NOT NULL CHECK(status IN (
        'pending','passed','failed','blocked','not_applicable'
    )),
    evidence_reference TEXT,
    evidence_sha256 TEXT,
    notes TEXT NOT NULL DEFAULT '',
    checked_by TEXT,
    checked_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(candidate_id)
        REFERENCES staging_candidates(candidate_id) ON DELETE CASCADE,
    FOREIGN KEY(checked_by) REFERENCES users(user_id),
    UNIQUE(candidate_id, check_code)
);

CREATE INDEX IF NOT EXISTS idx_staging_checks_candidate
ON staging_acceptance_checks(candidate_id, category, check_code);

CREATE TABLE IF NOT EXISTS staging_persistence_sentinels (
    sentinel_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    sentinel_key TEXT NOT NULL,
    sentinel_value_sha256 TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(candidate_id)
        REFERENCES staging_candidates(candidate_id) ON DELETE CASCADE,
    FOREIGN KEY(created_by) REFERENCES users(user_id),
    UNIQUE(candidate_id, sentinel_key)
);

CREATE TABLE IF NOT EXISTS staging_persistence_observations (
    observation_id TEXT PRIMARY KEY,
    sentinel_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    phase TEXT NOT NULL CHECK(phase IN (
        'before_restart','after_restart','after_redeploy'
    )),
    observed INTEGER NOT NULL CHECK(observed IN (0,1)),
    observed_sha256 TEXT,
    notes TEXT NOT NULL DEFAULT '',
    checked_by TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    FOREIGN KEY(sentinel_id)
        REFERENCES staging_persistence_sentinels(sentinel_id) ON DELETE CASCADE,
    FOREIGN KEY(candidate_id)
        REFERENCES staging_candidates(candidate_id) ON DELETE CASCADE,
    FOREIGN KEY(checked_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_staging_persistence_candidate
ON staging_persistence_observations(candidate_id, phase, checked_at);

CREATE TABLE IF NOT EXISTS staging_acceptance_decisions (
    decision_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    decision TEXT NOT NULL CHECK(decision IN ('accepted','rejected')),
    reason TEXT NOT NULL,
    blocker_summary_json TEXT NOT NULL,
    decided_by TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    FOREIGN KEY(candidate_id)
        REFERENCES staging_candidates(candidate_id) ON DELETE CASCADE,
    FOREIGN KEY(decided_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_staging_decisions_candidate
ON staging_acceptance_decisions(candidate_id, decided_at DESC);

CREATE TABLE IF NOT EXISTS beta_contacts (
    contact_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL CHECK(source_type IN (
        'access_request','beta_reservation','manual'
    )),
    source_id TEXT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    organization TEXT,
    relationship_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN (
        'new','contacted','interview_scheduled','interviewed',
        'pilot_candidate','pilot_active','declined','closed'
    )),
    owner_id TEXT,
    next_action_at TEXT,
    consent_contact INTEGER NOT NULL DEFAULT 0 CHECK(consent_contact IN (0,1)),
    consent_updates INTEGER NOT NULL DEFAULT 0 CHECK(consent_updates IN (0,1)),
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(owner_id) REFERENCES users(user_id),
    UNIQUE(source_type, source_id),
    UNIQUE(email, source_type)
);

CREATE INDEX IF NOT EXISTS idx_beta_contacts_status
ON beta_contacts(status, next_action_at);

CREATE TABLE IF NOT EXISTS beta_interviews (
    interview_id TEXT PRIMARY KEY,
    contact_id TEXT NOT NULL,
    interview_type TEXT NOT NULL CHECK(interview_type IN (
        'discovery','pilot_readiness','usability','post_pilot'
    )),
    scheduled_at TEXT,
    completed_at TEXT,
    interviewer_id TEXT NOT NULL,
    goals TEXT NOT NULL DEFAULT '',
    pains TEXT NOT NULL DEFAULT '',
    current_workflow TEXT NOT NULL DEFAULT '',
    success_criteria TEXT NOT NULL DEFAULT '',
    risk_notes TEXT NOT NULL DEFAULT '',
    decision TEXT NOT NULL CHECK(decision IN (
        'pending','continue','pilot_candidate','not_a_fit','follow_up'
    )),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(contact_id)
        REFERENCES beta_contacts(contact_id) ON DELETE CASCADE,
    FOREIGN KEY(interviewer_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_beta_interviews_contact
ON beta_interviews(contact_id, scheduled_at);

CREATE TABLE IF NOT EXISTS pilot_discovery_records (
    pilot_id TEXT PRIMARY KEY,
    contact_id TEXT NOT NULL,
    site_type TEXT NOT NULL,
    location_region TEXT,
    manual_workflow TEXT NOT NULL,
    available_infrastructure TEXT NOT NULL DEFAULT '',
    data_sources TEXT NOT NULL DEFAULT '',
    constraints TEXT NOT NULL DEFAULT '',
    proposed_scope TEXT NOT NULL,
    exclusion_scope TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN (
        'draft','reviewing','approved','declined','completed'
    )),
    approved_by TEXT,
    approved_at TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(contact_id)
        REFERENCES beta_contacts(contact_id) ON DELETE CASCADE,
    FOREIGN KEY(approved_by) REFERENCES users(user_id),
    FOREIGN KEY(created_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_pilot_discovery_status
ON pilot_discovery_records(status, updated_at DESC);

CREATE TABLE IF NOT EXISTS claims_register (
    claim_id TEXT PRIMARY KEY,
    claim_text TEXT NOT NULL,
    claim_type TEXT NOT NULL CHECK(claim_type IN (
        'product','research','quantum','agricultural','security','operational'
    )),
    evidence_level TEXT NOT NULL CHECK(evidence_level IN (
        'idea','prototype','simulation','controlled_beta',
        'field_verified','publication'
    )),
    status TEXT NOT NULL CHECK(status IN (
        'draft','approved','restricted','rejected','retired'
    )),
    evidence_reference TEXT,
    limitations TEXT NOT NULL,
    approved_by TEXT,
    approved_at TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(approved_by) REFERENCES users(user_id),
    FOREIGN KEY(created_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_claims_register_status
ON claims_register(status, evidence_level, updated_at DESC);

CREATE TABLE IF NOT EXISTS invitation_policies (
    policy_id TEXT PRIMARY KEY,
    version TEXT NOT NULL UNIQUE,
    active INTEGER NOT NULL DEFAULT 0 CHECK(active IN (0,1)),
    policy_json TEXT NOT NULL,
    approved_by TEXT,
    approved_at TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(approved_by) REFERENCES users(user_id),
    FOREIGN KEY(created_by) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_invitation_policy_active
ON invitation_policies(active) WHERE active=1;

CREATE TABLE IF NOT EXISTS demo_evidence_items (
    item_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    evidence_code TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN (
        'missing','captured','verified','rejected'
    )),
    file_reference TEXT,
    sha256 TEXT,
    notes TEXT NOT NULL DEFAULT '',
    captured_at TEXT,
    verified_by TEXT,
    verified_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(candidate_id)
        REFERENCES staging_candidates(candidate_id) ON DELETE CASCADE,
    FOREIGN KEY(verified_by) REFERENCES users(user_id),
    UNIQUE(candidate_id, evidence_code)
);

CREATE INDEX IF NOT EXISTS idx_demo_evidence_candidate
ON demo_evidence_items(candidate_id, evidence_code);

CREATE TABLE IF NOT EXISTS yc_update_snapshots (
    update_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    headline TEXT NOT NULL,
    summary TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    limitations TEXT NOT NULL,
    evidence_manifest_json TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(candidate_id)
        REFERENCES staging_candidates(candidate_id) ON DELETE CASCADE,
    FOREIGN KEY(created_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_yc_updates_candidate
ON yc_update_snapshots(candidate_id, created_at DESC);

CREATE TABLE IF NOT EXISTS controlled_beta_exports (
    export_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(candidate_id)
        REFERENCES staging_candidates(candidate_id) ON DELETE CASCADE,
    FOREIGN KEY(created_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_beta_exports_candidate
ON controlled_beta_exports(candidate_id, created_at DESC);

CREATE TRIGGER IF NOT EXISTS trg_staging_decisions_no_update
BEFORE UPDATE ON staging_acceptance_decisions
BEGIN
    SELECT RAISE(ABORT, 'Staging acceptance decisions are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_staging_decisions_no_delete
BEFORE DELETE ON staging_acceptance_decisions
BEGIN
    SELECT RAISE(ABORT, 'Staging acceptance decisions are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_persistence_observations_no_update
BEFORE UPDATE ON staging_persistence_observations
BEGIN
    SELECT RAISE(ABORT, 'Persistence observations are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_persistence_observations_no_delete
BEFORE DELETE ON staging_persistence_observations
BEGIN
    SELECT RAISE(ABORT, 'Persistence observations are immutable.');
END;
