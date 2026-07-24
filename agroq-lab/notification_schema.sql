CREATE TABLE IF NOT EXISTS admin_notification_preferences (
    user_id TEXT PRIMARY KEY,
    in_app_enabled INTEGER NOT NULL DEFAULT 1 CHECK(in_app_enabled IN (0,1)),
    email_enabled INTEGER NOT NULL DEFAULT 0 CHECK(email_enabled IN (0,1)),
    email_address TEXT,
    webhook_enabled INTEGER NOT NULL DEFAULT 0 CHECK(webhook_enabled IN (0,1)),
    web_push_enabled INTEGER NOT NULL DEFAULT 0 CHECK(web_push_enabled IN (0,1)),
    notify_login_success INTEGER NOT NULL DEFAULT 1 CHECK(notify_login_success IN (0,1)),
    notify_login_failure INTEGER NOT NULL DEFAULT 1 CHECK(notify_login_failure IN (0,1)),
    notify_access_changes INTEGER NOT NULL DEFAULT 1 CHECK(notify_access_changes IN (0,1)),
    notify_password_changes INTEGER NOT NULL DEFAULT 1 CHECK(notify_password_changes IN (0,1)),
    quiet_hours_start TEXT,
    quiet_hours_end TEXT,
    digest_mode TEXT NOT NULL DEFAULT 'immediate'
        CHECK(digest_mode IN ('immediate','hourly','daily')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS admin_notification_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('info','notice','warning','critical')),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    actor_user_id TEXT,
    actor_label TEXT,
    subject_user_id TEXT,
    source_entity_type TEXT,
    source_entity_id TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    dedupe_key TEXT,
    created_at TEXT NOT NULL,
    acknowledged_at TEXT,
    acknowledged_by TEXT,
    FOREIGN KEY(actor_user_id) REFERENCES users(user_id),
    FOREIGN KEY(subject_user_id) REFERENCES users(user_id),
    FOREIGN KEY(acknowledged_by) REFERENCES users(user_id),
    UNIQUE(dedupe_key)
);

CREATE INDEX IF NOT EXISTS idx_admin_notification_events_created
ON admin_notification_events(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_admin_notification_events_unread
ON admin_notification_events(acknowledged_at, created_at DESC);

CREATE TABLE IF NOT EXISTS admin_push_subscriptions (
    subscription_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    endpoint TEXT NOT NULL UNIQUE,
    p256dh TEXT NOT NULL,
    auth_secret TEXT NOT NULL,
    user_agent TEXT,
    device_label TEXT,
    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
    created_at TEXT NOT NULL,
    last_success_at TEXT,
    last_failure_at TEXT,
    last_failure_reason TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_admin_push_subscriptions_user
ON admin_push_subscriptions(user_id, active);

CREATE TABLE IF NOT EXISTS admin_notification_deliveries (
    delivery_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    channel TEXT NOT NULL CHECK(channel IN ('email','webhook','web_push')),
    destination_label TEXT,
    status TEXT NOT NULL CHECK(status IN ('pending','sent','failed','skipped')),
    attempt_count INTEGER NOT NULL DEFAULT 0,
    last_attempt_at TEXT,
    delivered_at TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(event_id) REFERENCES admin_notification_events(event_id),
    UNIQUE(event_id, channel, destination_label)
);

CREATE INDEX IF NOT EXISTS idx_admin_notification_deliveries_pending
ON admin_notification_deliveries(status, created_at);

CREATE TRIGGER IF NOT EXISTS trg_agroq_audit_admin_notification
AFTER INSERT ON audit_events
WHEN
    lower(NEW.action) = 'login'
    OR lower(NEW.action) LIKE '%access%'
    OR lower(NEW.action) LIKE '%invite%'
    OR lower(NEW.action) LIKE '%account%'
    OR lower(NEW.action) LIKE '%user_created%'
    OR lower(NEW.action) LIKE '%profile%'
    OR lower(NEW.action) LIKE '%password%'
    OR lower(NEW.action) LIKE '%role%'
BEGIN
    INSERT OR IGNORE INTO admin_notification_events(
        event_id,
        event_type,
        severity,
        title,
        body,
        actor_user_id,
        actor_label,
        subject_user_id,
        source_entity_type,
        source_entity_id,
        metadata_json,
        dedupe_key,
        created_at
    ) VALUES(
        'AGQ-NOTIFY-' || lower(hex(randomblob(16))),
        CASE
            WHEN lower(NEW.action) = 'login' THEN 'login_success'
            WHEN lower(NEW.action) LIKE '%password%' THEN 'password_change'
            WHEN lower(NEW.action) LIKE '%access%' THEN 'access_activity'
            WHEN lower(NEW.action) LIKE '%invite%' THEN 'invitation_activity'
            WHEN lower(NEW.action) LIKE '%role%' THEN 'role_change'
            ELSE 'account_activity'
        END,
        CASE
            WHEN lower(NEW.action) LIKE '%password%' THEN 'warning'
            WHEN lower(NEW.action) LIKE '%role%' THEN 'warning'
            ELSE 'notice'
        END,
        CASE
            WHEN lower(NEW.action) = 'login' THEN 'AgroQ account signed in'
            WHEN lower(NEW.action) LIKE '%password%' THEN 'AgroQ password activity'
            WHEN lower(NEW.action) LIKE '%access%' THEN 'New AgroQ access activity'
            WHEN lower(NEW.action) LIKE '%invite%' THEN 'AgroQ invitation activity'
            WHEN lower(NEW.action) LIKE '%role%' THEN 'AgroQ role changed'
            ELSE 'AgroQ account activity'
        END,
        'Action: ' || NEW.action,
        NEW.user_id,
        NULL,
        NEW.user_id,
        NEW.entity_type,
        NEW.entity_id,
        COALESCE(NEW.details, '{}'),
        'audit:' || NEW.audit_id,
        NEW.created_at
    );
END;
