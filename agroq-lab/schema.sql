CREATE TABLE IF NOT EXISTS sites (
    site_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT,
    status TEXT NOT NULL,
    owner TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('administrator', 'researcher', 'field_operator', 'viewer')),
    site_id TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY(site_id) REFERENCES sites(site_id)
);

CREATE TABLE IF NOT EXISTS audit_events (
    audit_id TEXT PRIMARY KEY,
    user_id TEXT,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    details TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS plots (
    plot_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    plot_type TEXT NOT NULL,
    area TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assets (
    asset_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    plot_id TEXT,
    status TEXT NOT NULL,
    revision TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(plot_id) REFERENCES plots(plot_id)
);

CREATE TABLE IF NOT EXISTS experiments (
    experiment_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    hypothesis TEXT,
    status TEXT NOT NULL,
    plot_id TEXT,
    owner TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(plot_id) REFERENCES plots(plot_id)
);

CREATE TABLE IF NOT EXISTS observations (
    observation_id TEXT PRIMARY KEY,
    plot_id TEXT NOT NULL,
    asset_id TEXT,
    observed_property TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK(source_type IN ('manual','sensor','laboratory','import')),
    quality_flag TEXT NOT NULL,
    notes TEXT,
    observed_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(plot_id) REFERENCES plots(plot_id),
    FOREIGN KEY(asset_id) REFERENCES assets(asset_id)
);

CREATE TABLE IF NOT EXISTS sync_submissions (
    sync_id TEXT PRIMARY KEY,
    client_request_id TEXT NOT NULL UNIQUE,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('observation')),
    payload_json TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('applied','conflict','rejected','resolved')),
    result_entity_id TEXT,
    conflict_reason TEXT,
    submitted_by TEXT NOT NULL,
    submitted_at TEXT NOT NULL,
    resolved_by TEXT,
    resolved_at TEXT,
    resolution TEXT CHECK(resolution IS NULL OR resolution IN ('accepted_as_new','dismissed')),
    resolution_notes TEXT,
    FOREIGN KEY(submitted_by) REFERENCES users(user_id),
    FOREIGN KEY(resolved_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS gateway_devices (
    device_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    device_type TEXT NOT NULL,
    network_address TEXT,
    status TEXT NOT NULL CHECK(status IN ('registered','online','offline','maintenance','retired')),
    firmware_version TEXT,
    notes TEXT,
    last_seen_at TEXT,
    registered_by TEXT NOT NULL,
    registered_at TEXT NOT NULL,
    FOREIGN KEY(registered_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_gateway_devices_status
ON gateway_devices(status, last_seen_at);

CREATE TABLE IF NOT EXISTS backup_runs (
    backup_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE,
    trigger_type TEXT NOT NULL CHECK(trigger_type IN ('manual','automatic')),
    status TEXT NOT NULL CHECK(status IN ('verified','failed')),
    size_bytes INTEGER NOT NULL DEFAULT 0,
    verification_message TEXT,
    created_by TEXT,
    created_at TEXT NOT NULL,
    verified_at TEXT,
    FOREIGN KEY(created_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_backup_runs_created_at ON backup_runs(created_at);

CREATE TABLE IF NOT EXISTS treatments (
    treatment_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    is_control INTEGER NOT NULL DEFAULT 0,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(experiment_id) REFERENCES experiments(experiment_id),
    FOREIGN KEY(created_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS treatment_assignments (
    assignment_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    treatment_id TEXT NOT NULL,
    plot_id TEXT NOT NULL,
    responsible_user_id TEXT NOT NULL,
    assigned_at TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    notes TEXT,
    FOREIGN KEY(experiment_id) REFERENCES experiments(experiment_id),
    FOREIGN KEY(treatment_id) REFERENCES treatments(treatment_id),
    FOREIGN KEY(plot_id) REFERENCES plots(plot_id),
    FOREIGN KEY(responsible_user_id) REFERENCES users(user_id),
    UNIQUE(experiment_id, plot_id)
);

CREATE TABLE IF NOT EXISTS experiment_status_history (
    status_event_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    previous_status TEXT NOT NULL,
    new_status TEXT NOT NULL,
    reason TEXT NOT NULL,
    changed_by TEXT NOT NULL,
    changed_at TEXT NOT NULL,
    FOREIGN KEY(experiment_id) REFERENCES experiments(experiment_id),
    FOREIGN KEY(changed_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS experiment_outcomes (
    outcome_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    assignment_id TEXT,
    observation_id TEXT NOT NULL,
    interpretation TEXT,
    recorded_by TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY(experiment_id) REFERENCES experiments(experiment_id),
    FOREIGN KEY(assignment_id) REFERENCES treatment_assignments(assignment_id),
    FOREIGN KEY(observation_id) REFERENCES observations(observation_id),
    FOREIGN KEY(recorded_by) REFERENCES users(user_id),
    UNIQUE(experiment_id, observation_id)
);

CREATE TABLE IF NOT EXISTS samples (
    sample_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    assignment_id TEXT,
    treatment_id TEXT,
    plot_id TEXT NOT NULL,
    sample_type TEXT NOT NULL,
    collection_method TEXT NOT NULL,
    collected_by TEXT NOT NULL,
    collected_at TEXT NOT NULL,
    storage_location TEXT,
    status TEXT NOT NULL CHECK(status IN ('collected','stored','in_analysis','analyzed','disposed')),
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(experiment_id) REFERENCES experiments(experiment_id),
    FOREIGN KEY(assignment_id) REFERENCES treatment_assignments(assignment_id),
    FOREIGN KEY(treatment_id) REFERENCES treatments(treatment_id),
    FOREIGN KEY(plot_id) REFERENCES plots(plot_id),
    FOREIGN KEY(collected_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS sample_status_history (
    status_event_id TEXT PRIMARY KEY,
    sample_id TEXT NOT NULL,
    previous_status TEXT NOT NULL,
    new_status TEXT NOT NULL,
    reason TEXT NOT NULL,
    changed_by TEXT NOT NULL,
    changed_at TEXT NOT NULL,
    FOREIGN KEY(sample_id) REFERENCES samples(sample_id),
    FOREIGN KEY(changed_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS evidence_attachments (
    attachment_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('sample','observation','manual_task','experiment')),
    entity_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    media_type TEXT,
    storage_reference TEXT NOT NULL,
    sha256 TEXT,
    description TEXT,
    captured_at TEXT,
    recorded_by TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY(recorded_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS observation_corrections (
    correction_id TEXT PRIMARY KEY,
    observation_id TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    quality_flag TEXT NOT NULL,
    notes TEXT,
    reason TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(observation_id) REFERENCES observations(observation_id),
    FOREIGN KEY(created_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS manual_tasks (
    task_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    task_type TEXT NOT NULL,
    plot_id TEXT,
    status TEXT NOT NULL,
    priority TEXT NOT NULL,
    assigned_to TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    FOREIGN KEY(plot_id) REFERENCES plots(plot_id)
);

CREATE TABLE IF NOT EXISTS manual_task_details (
    task_id TEXT PRIMARY KEY,
    asset_id TEXT,
    experiment_id TEXT,
    assigned_user_id TEXT,
    due_at TEXT,
    requires_approval INTEGER NOT NULL DEFAULT 0,
    created_by TEXT NOT NULL,
    FOREIGN KEY(task_id) REFERENCES manual_tasks(task_id),
    FOREIGN KEY(asset_id) REFERENCES assets(asset_id),
    FOREIGN KEY(experiment_id) REFERENCES experiments(experiment_id),
    FOREIGN KEY(assigned_user_id) REFERENCES users(user_id),
    FOREIGN KEY(created_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS manual_task_status_history (
    status_event_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    previous_status TEXT NOT NULL,
    new_status TEXT NOT NULL,
    reason TEXT NOT NULL,
    changed_by TEXT NOT NULL,
    changed_at TEXT NOT NULL,
    FOREIGN KEY(task_id) REFERENCES manual_tasks(task_id),
    FOREIGN KEY(changed_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS manual_task_evidence (
    evidence_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    reference TEXT NOT NULL,
    notes TEXT,
    recorded_by TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY(task_id) REFERENCES manual_tasks(task_id),
    FOREIGN KEY(recorded_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS manual_task_approvals (
    approval_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    decision TEXT NOT NULL CHECK(decision IN ('approved','rejected')),
    reason TEXT NOT NULL,
    reviewer_id TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    FOREIGN KEY(task_id) REFERENCES manual_tasks(task_id),
    FOREIGN KEY(reviewer_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS outage_tests (
    outage_test_id TEXT PRIMARY KEY,
    status TEXT NOT NULL CHECK(status IN ('running','passed','failed')),
    started_at TEXT NOT NULL,
    started_by TEXT NOT NULL,
    completed_at TEXT,
    completed_by TEXT,
    notes TEXT,
    result_notes TEXT,
    FOREIGN KEY(started_by) REFERENCES users(user_id),
    FOREIGN KEY(completed_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS outage_checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    outage_test_id TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    database_ok INTEGER NOT NULL CHECK(database_ok IN (0,1)),
    manual_workflow_ok INTEGER NOT NULL CHECK(manual_workflow_ok IN (0,1)),
    backup_ok INTEGER NOT NULL CHECK(backup_ok IN (0,1)),
    notes TEXT,
    recorded_by TEXT NOT NULL,
    FOREIGN KEY(outage_test_id) REFERENCES outage_tests(outage_test_id),
    FOREIGN KEY(recorded_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    rationale TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_version TEXT NOT NULL,
    confidence TEXT,
    approval_status TEXT NOT NULL,
    plot_id TEXT,
    decided_by TEXT,
    decision_notes TEXT,
    created_at TEXT NOT NULL,
    decided_at TEXT,
    FOREIGN KEY(plot_id) REFERENCES plots(plot_id)
);

CREATE INDEX IF NOT EXISTS idx_users_username
ON users(username);

CREATE INDEX IF NOT EXISTS idx_users_site_id
ON users(site_id);

CREATE INDEX IF NOT EXISTS idx_audit_events_created_at
ON audit_events(created_at);

CREATE INDEX IF NOT EXISTS idx_sync_submissions_status
ON sync_submissions(status, submitted_at);

CREATE INDEX IF NOT EXISTS idx_observations_plot_time
ON observations(plot_id, observed_at);

CREATE INDEX IF NOT EXISTS idx_observation_corrections_observation
ON observation_corrections(observation_id, created_at);

CREATE INDEX IF NOT EXISTS idx_treatments_experiment
ON treatments(experiment_id);

CREATE INDEX IF NOT EXISTS idx_assignments_experiment
ON treatment_assignments(experiment_id);

CREATE INDEX IF NOT EXISTS idx_experiment_status_history
ON experiment_status_history(experiment_id, changed_at);

CREATE INDEX IF NOT EXISTS idx_experiment_outcomes
ON experiment_outcomes(experiment_id, recorded_at);

CREATE INDEX IF NOT EXISTS idx_samples_experiment
ON samples(experiment_id, collected_at);

CREATE INDEX IF NOT EXISTS idx_samples_plot
ON samples(plot_id, collected_at);

CREATE INDEX IF NOT EXISTS idx_sample_status_history
ON sample_status_history(sample_id, changed_at);

CREATE INDEX IF NOT EXISTS idx_evidence_attachments_entity
ON evidence_attachments(entity_type, entity_id, recorded_at);

CREATE INDEX IF NOT EXISTS idx_tasks_status
ON manual_tasks(status);

CREATE INDEX IF NOT EXISTS idx_task_history_task
ON manual_task_status_history(task_id, changed_at);

CREATE INDEX IF NOT EXISTS idx_task_evidence_task
ON manual_task_evidence(task_id, recorded_at);

CREATE INDEX IF NOT EXISTS idx_task_approvals_task
ON manual_task_approvals(task_id, reviewed_at);

CREATE INDEX IF NOT EXISTS idx_recommendations_approval
ON recommendations(approval_status);

CREATE INDEX IF NOT EXISTS idx_outage_tests_started
ON outage_tests(started_at);

CREATE INDEX IF NOT EXISTS idx_outage_checkpoints_test
ON outage_checkpoints(outage_test_id, recorded_at);
