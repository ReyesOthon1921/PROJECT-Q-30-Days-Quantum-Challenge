-- AgroQ Q20-Q22 controlled-pilot activation, learning, and exit schema.

CREATE TABLE IF NOT EXISTS pilot_enrollments (
    enrollment_id TEXT PRIMARY KEY,
    pilot_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    contact_id TEXT NOT NULL,
    participant_user_id TEXT,
    cohort_name TEXT NOT NULL,
    scope TEXT NOT NULL,
    exclusion_scope TEXT NOT NULL,
    support_owner_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN (
        'draft','onboarding','active','paused','completed','withdrawn'
    )),
    activation_reason TEXT NOT NULL DEFAULT '',
    activated_by TEXT,
    activated_at TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(pilot_id) REFERENCES pilot_discovery_records(pilot_id),
    FOREIGN KEY(candidate_id) REFERENCES staging_candidates(candidate_id),
    FOREIGN KEY(contact_id) REFERENCES beta_contacts(contact_id),
    FOREIGN KEY(participant_user_id) REFERENCES users(user_id),
    FOREIGN KEY(support_owner_id) REFERENCES users(user_id),
    FOREIGN KEY(activated_by) REFERENCES users(user_id),
    FOREIGN KEY(created_by) REFERENCES users(user_id),
    UNIQUE(pilot_id, candidate_id)
);

CREATE INDEX IF NOT EXISTS idx_pilot_enrollments_status
ON pilot_enrollments(status, updated_at DESC);

CREATE TABLE IF NOT EXISTS pilot_onboarding_checks (
    check_id TEXT PRIMARY KEY,
    enrollment_id TEXT NOT NULL,
    check_code TEXT NOT NULL,
    title TEXT NOT NULL,
    required INTEGER NOT NULL CHECK(required IN (0,1)),
    status TEXT NOT NULL CHECK(status IN (
        'pending','completed','blocked','not_applicable'
    )),
    evidence_reference TEXT,
    notes TEXT NOT NULL DEFAULT '',
    verified_by TEXT,
    verified_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(enrollment_id)
        REFERENCES pilot_enrollments(enrollment_id) ON DELETE CASCADE,
    FOREIGN KEY(verified_by) REFERENCES users(user_id),
    UNIQUE(enrollment_id, check_code)
);

CREATE TABLE IF NOT EXISTS pilot_acknowledgments (
    acknowledgment_id TEXT PRIMARY KEY,
    enrollment_id TEXT NOT NULL,
    acknowledgment_type TEXT NOT NULL CHECK(acknowledgment_type IN (
        'data_handling','human_control','research_limitations'
    )),
    version TEXT NOT NULL,
    accepted INTEGER NOT NULL CHECK(accepted IN (0,1)),
    evidence_reference TEXT NOT NULL,
    acknowledged_by TEXT NOT NULL,
    acknowledged_at TEXT NOT NULL,
    FOREIGN KEY(enrollment_id)
        REFERENCES pilot_enrollments(enrollment_id) ON DELETE CASCADE,
    FOREIGN KEY(acknowledged_by) REFERENCES users(user_id),
    UNIQUE(enrollment_id, acknowledgment_type, version)
);

CREATE TABLE IF NOT EXISTS pilot_status_events (
    event_id TEXT PRIMARY KEY,
    enrollment_id TEXT NOT NULL,
    previous_status TEXT,
    new_status TEXT NOT NULL CHECK(new_status IN (
        'draft','onboarding','active','paused','completed','withdrawn'
    )),
    reason TEXT NOT NULL,
    recorded_by TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY(enrollment_id)
        REFERENCES pilot_enrollments(enrollment_id) ON DELETE CASCADE,
    FOREIGN KEY(recorded_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS pilot_feedback (
    feedback_id TEXT PRIMARY KEY,
    enrollment_id TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN (
        'usability','workflow','data_quality','research','support','other'
    )),
    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
    description TEXT NOT NULL,
    context TEXT NOT NULL DEFAULT '',
    evidence_reference TEXT,
    submitted_by TEXT NOT NULL,
    submitted_at TEXT NOT NULL,
    FOREIGN KEY(enrollment_id)
        REFERENCES pilot_enrollments(enrollment_id) ON DELETE CASCADE,
    FOREIGN KEY(submitted_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS pilot_feedback_reviews (
    review_id TEXT PRIMARY KEY,
    feedback_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN (
        'new','triaged','planned','resolved','closed'
    )),
    disposition TEXT NOT NULL DEFAULT '',
    reviewed_by TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    FOREIGN KEY(feedback_id)
        REFERENCES pilot_feedback(feedback_id) ON DELETE CASCADE,
    FOREIGN KEY(reviewed_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS pilot_incidents (
    incident_id TEXT PRIMARY KEY,
    enrollment_id TEXT NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN (
        'low','medium','high','critical'
    )),
    category TEXT NOT NULL CHECK(category IN (
        'access','privacy','data_integrity','availability',
        'workflow','field_safety','other'
    )),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    impact TEXT NOT NULL,
    immediate_manual_action TEXT NOT NULL,
    evidence_reference TEXT,
    reported_by TEXT NOT NULL,
    reported_at TEXT NOT NULL,
    FOREIGN KEY(enrollment_id)
        REFERENCES pilot_enrollments(enrollment_id) ON DELETE CASCADE,
    FOREIGN KEY(reported_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS pilot_incident_events (
    event_id TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN (
        'open','triaged','contained','resolved','closed'
    )),
    notes TEXT NOT NULL,
    evidence_reference TEXT,
    recorded_by TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY(incident_id)
        REFERENCES pilot_incidents(incident_id) ON DELETE CASCADE,
    FOREIGN KEY(recorded_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS pilot_metric_observations (
    metric_id TEXT PRIMARY KEY,
    enrollment_id TEXT NOT NULL,
    metric_code TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    baseline_value REAL,
    target_value REAL,
    observed_value REAL NOT NULL,
    unit TEXT NOT NULL,
    direction TEXT NOT NULL CHECK(direction IN (
        'higher','lower','range','informational'
    )),
    evidence_reference TEXT NOT NULL,
    evidence_sha256 TEXT NOT NULL,
    limitations TEXT NOT NULL,
    captured_by TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    FOREIGN KEY(enrollment_id)
        REFERENCES pilot_enrollments(enrollment_id) ON DELETE CASCADE,
    FOREIGN KEY(captured_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_pilot_metrics_enrollment
ON pilot_metric_observations(enrollment_id, metric_code, captured_at DESC);

CREATE TABLE IF NOT EXISTS pilot_exit_decisions (
    decision_id TEXT PRIMARY KEY,
    enrollment_id TEXT NOT NULL,
    decision TEXT NOT NULL CHECK(decision IN (
        'continue','extend','pause','complete','stop',
        'recommend_release_review'
    )),
    reason TEXT NOT NULL,
    blocker_summary_json TEXT NOT NULL,
    decided_by TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    FOREIGN KEY(enrollment_id)
        REFERENCES pilot_enrollments(enrollment_id) ON DELETE CASCADE,
    FOREIGN KEY(decided_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS pilot_evidence_exports (
    export_id TEXT PRIMARY KEY,
    enrollment_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(enrollment_id)
        REFERENCES pilot_enrollments(enrollment_id) ON DELETE CASCADE,
    FOREIGN KEY(created_by) REFERENCES users(user_id)
);

CREATE TRIGGER IF NOT EXISTS trg_pilot_ack_no_update
BEFORE UPDATE ON pilot_acknowledgments
BEGIN
    SELECT RAISE(ABORT, 'Pilot acknowledgments are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_pilot_ack_no_delete
BEFORE DELETE ON pilot_acknowledgments
BEGIN
    SELECT RAISE(ABORT, 'Pilot acknowledgments are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_pilot_feedback_no_update
BEFORE UPDATE ON pilot_feedback
BEGIN
    SELECT RAISE(ABORT, 'Pilot feedback submissions are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_pilot_incident_no_update
BEFORE UPDATE ON pilot_incidents
BEGIN
    SELECT RAISE(ABORT, 'Pilot incident reports are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_pilot_metrics_no_update
BEFORE UPDATE ON pilot_metric_observations
BEGIN
    SELECT RAISE(ABORT, 'Pilot metric observations are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_pilot_exit_no_update
BEFORE UPDATE ON pilot_exit_decisions
BEGIN
    SELECT RAISE(ABORT, 'Pilot exit decisions are immutable.');
END;
