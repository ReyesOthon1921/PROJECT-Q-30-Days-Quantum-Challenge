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

CREATE TABLE IF NOT EXISTS device_health_events (
    health_event_id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK(event_type IN ('heartbeat','inspection','status_change')),
    previous_status TEXT,
    reported_status TEXT NOT NULL CHECK(reported_status IN ('registered','online','offline','maintenance','retired')),
    diagnostic_result TEXT CHECK(diagnostic_result IS NULL OR diagnostic_result IN ('pass','warning','fail','not_run')),
    battery_percent REAL CHECK(battery_percent IS NULL OR (battery_percent >= 0 AND battery_percent <= 100)),
    signal_quality REAL CHECK(signal_quality IS NULL OR (signal_quality >= 0 AND signal_quality <= 100)),
    firmware_version TEXT,
    notes TEXT,
    recorded_by TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY(device_id) REFERENCES gateway_devices(device_id),
    FOREIGN KEY(recorded_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_device_health_events_device
ON device_health_events(device_id, recorded_at);

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

-- AgroQ Q11-Q13 persistent quantum backend, runner, and lineage schema.

CREATE TABLE IF NOT EXISTS quantum_research_sources (
    source_id TEXT PRIMARY KEY,
    sequence_json TEXT NOT NULL,
    title TEXT NOT NULL,
    authors_json TEXT NOT NULL,
    year INTEGER,
    venue TEXT,
    publication_status TEXT,
    identifier TEXT,
    url TEXT,
    mechanism TEXT,
    agroq_feature TEXT,
    reproduction_target TEXT,
    evidence_status TEXT NOT NULL,
    limitations TEXT,
    acknowledgment TEXT,
    endorsement_boundary TEXT,
    tags_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS quantum_datasets (
    dataset_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source_kind TEXT NOT NULL,
    source_tables_json TEXT NOT NULL,
    source_record_ids_json TEXT NOT NULL,
    snapshot_json TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    record_count INTEGER NOT NULL CHECK(record_count > 0),
    quality_summary_json TEXT NOT NULL,
    permitted_families_json TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    review_status TEXT NOT NULL CHECK(review_status IN ('pending','approved','rejected')),
    FOREIGN KEY(created_by) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_quantum_datasets_sha256
ON quantum_datasets(sha256);

CREATE INDEX IF NOT EXISTS idx_quantum_datasets_created_at
ON quantum_datasets(created_at DESC);

CREATE TABLE IF NOT EXISTS quantum_dataset_lineage (
    dataset_id TEXT NOT NULL,
    source_table TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    PRIMARY KEY(dataset_id, source_table, source_record_id),
    FOREIGN KEY(dataset_id) REFERENCES quantum_datasets(dataset_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_quantum_dataset_lineage_source
ON quantum_dataset_lineage(source_table, source_record_id);

CREATE TABLE IF NOT EXISTS quantum_experiments (
    experiment_id TEXT PRIMARY KEY,
    sequence TEXT NOT NULL CHECK(sequence IN ('Q2','Q3','Q4','Q5','Q6','Q7','Q8','Q9','Q10')),
    title TEXT NOT NULL,
    problem_family TEXT NOT NULL,
    source_ids_json TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN (
        'Planned','Registered','Ready for baseline','Simulation complete',
        'Registry complete','Archived'
    )),
    run_type TEXT NOT NULL CHECK(run_type IN (
        'classical','quantum-inspired','quantum-simulator',
        'quantum-hardware','standards-registry'
    )),
    algorithm TEXT,
    dataset_id TEXT,
    formulation_json TEXT NOT NULL,
    formulation_sha256 TEXT NOT NULL,
    code_commit TEXT NOT NULL,
    claim_controls_json TEXT NOT NULL,
    notes TEXT,
    raw_record_json TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(dataset_id) REFERENCES quantum_datasets(dataset_id),
    FOREIGN KEY(created_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_quantum_experiments_sequence
ON quantum_experiments(sequence, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_quantum_experiments_dataset
ON quantum_experiments(dataset_id);

CREATE TABLE IF NOT EXISTS quantum_runs (
    run_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    algorithm TEXT,
    run_type TEXT NOT NULL,
    seed INTEGER,
    run_budget_json TEXT NOT NULL,
    configuration_json TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('queued','running','completed','failed','cancelled')),
    started_at TEXT NOT NULL,
    completed_at TEXT,
    runtime_seconds REAL,
    result_sha256 TEXT,
    error_message TEXT,
    created_by TEXT NOT NULL,
    FOREIGN KEY(experiment_id) REFERENCES quantum_experiments(experiment_id) ON DELETE CASCADE,
    FOREIGN KEY(created_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_quantum_runs_experiment
ON quantum_runs(experiment_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_quantum_runs_status
ON quantum_runs(status, started_at DESC);

CREATE TABLE IF NOT EXISTS quantum_solver_results (
    result_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    solver_name TEXT NOT NULL,
    result_json TEXT NOT NULL,
    objective REAL,
    feasible INTEGER NOT NULL CHECK(feasible IN (0,1)),
    constraint_violations INTEGER NOT NULL DEFAULT 0,
    approximation_gap REAL,
    runtime_seconds REAL,
    FOREIGN KEY(run_id) REFERENCES quantum_runs(run_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_quantum_solver_results_run
ON quantum_solver_results(run_id, solver_name);

CREATE TABLE IF NOT EXISTS quantum_artifacts (
    artifact_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    filename TEXT NOT NULL,
    media_type TEXT NOT NULL,
    content_text TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES quantum_runs(run_id) ON DELETE CASCADE,
    UNIQUE(run_id, filename)
);

CREATE INDEX IF NOT EXISTS idx_quantum_artifacts_run
ON quantum_artifacts(run_id, created_at);

CREATE TABLE IF NOT EXISTS quantum_reviews (
    review_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    decision TEXT NOT NULL CHECK(decision IN (
        'approved_for_research','rejected','needs_revision'
    )),
    notes TEXT NOT NULL,
    reviewer_id TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES quantum_runs(run_id) ON DELETE CASCADE,
    FOREIGN KEY(reviewer_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_quantum_reviews_run
ON quantum_reviews(run_id, reviewed_at DESC);

CREATE TABLE IF NOT EXISTS quantum_claim_controls (
    run_id TEXT PRIMARY KEY,
    simulator_only INTEGER NOT NULL CHECK(simulator_only IN (0,1)),
    hardware_used INTEGER NOT NULL CHECK(hardware_used IN (0,1)),
    advantage_claim INTEGER NOT NULL CHECK(advantage_claim IN (0,1)),
    operational_dependency INTEGER NOT NULL CHECK(operational_dependency IN (0,1)),
    matched_budget INTEGER NOT NULL CHECK(matched_budget IN (0,1)),
    classical_baseline_required INTEGER NOT NULL CHECK(classical_baseline_required IN (0,1)),
    synthetic_data INTEGER NOT NULL CHECK(synthetic_data IN (0,1)),
    human_review_required INTEGER NOT NULL CHECK(human_review_required IN (0,1)),
    FOREIGN KEY(run_id) REFERENCES quantum_runs(run_id) ON DELETE CASCADE,
    CHECK(advantage_claim = 0),
    CHECK(operational_dependency = 0)
);

-- AgroQ Q14 validation, regression, and scientific-gate schema.

CREATE TABLE IF NOT EXISTS quantum_validation_events (
    validation_id TEXT PRIMARY KEY,
    run_id TEXT,
    dataset_id TEXT,
    gate_type TEXT NOT NULL CHECK(gate_type IN (
        'dataset_integrity','classical_baseline',
        'deterministic_replay','scientific_release'
    )),
    status TEXT NOT NULL CHECK(status IN ('passed','warning','failed')),
    message TEXT NOT NULL,
    report_json TEXT NOT NULL,
    evaluated_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES quantum_runs(run_id) ON DELETE CASCADE,
    FOREIGN KEY(dataset_id) REFERENCES quantum_datasets(dataset_id) ON DELETE CASCADE,
    FOREIGN KEY(evaluated_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_quantum_validation_run
ON quantum_validation_events(run_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_quantum_validation_dataset
ON quantum_validation_events(dataset_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_quantum_validation_status
ON quantum_validation_events(status, created_at DESC);

CREATE TABLE IF NOT EXISTS quantum_replay_checks (
    replay_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    expected_result_sha256 TEXT,
    replay_result_sha256 TEXT,
    deterministic INTEGER NOT NULL CHECK(deterministic IN (0,1)),
    configuration_sha256 TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES quantum_runs(run_id) ON DELETE CASCADE,
    FOREIGN KEY(created_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_quantum_replay_run
ON quantum_replay_checks(run_id, created_at DESC);
