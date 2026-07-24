CREATE TABLE IF NOT EXISTS access_requests (
    request_id TEXT PRIMARY KEY,
    relationship_type TEXT NOT NULL CHECK(
        relationship_type IN ('beta_tester','investor','contributor','partner','researcher','customer')
    ),
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    organization TEXT,
    role_title TEXT,
    message TEXT,
    consent_contact INTEGER NOT NULL DEFAULT 0,
    consent_updates INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'new' CHECK(
        status IN ('new','reviewing','approved','declined','archived')
    ),
    created_at TEXT NOT NULL,
    reviewed_by TEXT,
    reviewed_at TEXT,
    FOREIGN KEY(reviewed_by) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_access_requests_status_created
ON access_requests(status, created_at);

CREATE TABLE IF NOT EXISTS invite_codes (
    invite_id TEXT PRIMARY KEY,
    code_hash TEXT NOT NULL UNIQUE,
    code_hint TEXT NOT NULL,
    relationship_type TEXT NOT NULL CHECK(
        relationship_type IN ('beta_tester','investor','contributor','partner','researcher','customer')
    ),
    role TEXT NOT NULL CHECK(role IN ('viewer','researcher','field_operator')),
    email TEXT,
    expires_at TEXT NOT NULL,
    max_uses INTEGER NOT NULL DEFAULT 1,
    use_count INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    note TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_used_at TEXT,
    FOREIGN KEY(created_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id TEXT PRIMARY KEY,
    relationship_type TEXT NOT NULL CHECK(
        relationship_type IN ('founder','beta_tester','investor','contributor','partner','researcher','customer','field_staff')
    ),
    email TEXT NOT NULL UNIQUE,
    organization TEXT,
    role_title TEXT,
    bio TEXT,
    github_url TEXT,
    linkedin_url TEXT,
    privacy_level TEXT NOT NULL DEFAULT 'private' CHECK(
        privacy_level IN ('private','team','community')
    ),
    consent_contact INTEGER NOT NULL DEFAULT 0,
    consent_updates INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS beta_reservations (
    reservation_id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    full_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'interest_recorded',
    notes TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS temporary_login_tokens (
    token_id TEXT PRIMARY KEY,
    token_hash TEXT NOT NULL UNIQUE,
    user_id TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);
