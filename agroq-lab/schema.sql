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

CREATE INDEX IF NOT EXISTS idx_observations_plot_time
ON observations(plot_id, observed_at);

CREATE INDEX IF NOT EXISTS idx_tasks_status
ON manual_tasks(status);

CREATE INDEX IF NOT EXISTS idx_recommendations_approval
ON recommendations(approval_status);
