CREATE TABLE IF NOT EXISTS lead_followups (
    source_type TEXT NOT NULL CHECK(
        source_type IN ('access_request','beta_reservation','founding_program')
    ),
    source_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new' CHECK(
        status IN (
            'new','reviewing','contacted','meeting_scheduled','proposal_sent',
            'waiting_on_customer','onboarded','closed','not_a_fit'
        )
    ),
    priority TEXT NOT NULL DEFAULT 'normal' CHECK(
        priority IN ('low','normal','high','urgent')
    ),
    assigned_to TEXT,
    contact_method TEXT,
    last_contacted_at TEXT,
    next_follow_up_at TEXT,
    follow_up_notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by TEXT,
    PRIMARY KEY(source_type, source_id),
    FOREIGN KEY(updated_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_lead_followups_status_due
ON lead_followups(status, next_follow_up_at);

CREATE TABLE IF NOT EXISTS lead_followup_history (
    history_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    previous_status TEXT,
    new_status TEXT NOT NULL,
    priority TEXT NOT NULL,
    contact_method TEXT,
    note TEXT,
    next_follow_up_at TEXT,
    changed_by TEXT,
    changed_at TEXT NOT NULL,
    FOREIGN KEY(changed_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_lead_followup_history_source
ON lead_followup_history(source_type, source_id, changed_at DESC);
