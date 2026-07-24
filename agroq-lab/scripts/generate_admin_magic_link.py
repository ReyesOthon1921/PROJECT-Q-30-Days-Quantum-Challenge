from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import os
from pathlib import Path
import secrets
import sqlite3
import sys


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.environ.get("AGROQ_DB_PATH", BASE_DIR / "instance" / "agroq.db"))
SCHEMA_PATH = BASE_DIR / "access_schema.sql"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a one-time AgroQ administrator sign-in link."
    )
    parser.add_argument("--username", default="admin")
    parser.add_argument("--minutes", type=int, default=15)
    parser.add_argument(
        "--base-url",
        default=os.environ.get("AGROQ_PUBLIC_URL", "http://127.0.0.1:5000"),
    )
    args = parser.parse_args()

    if not DB_PATH.is_file():
        print(f"Database not found: {DB_PATH}")
        return 1

    minutes = max(5, min(60, args.minutes))
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        user = connection.execute(
            "SELECT * FROM users WHERE username=? AND role='administrator' AND active=1",
            (args.username,),
        ).fetchone()
        if user is None:
            print(f"Active administrator not found: {args.username}")
            print("Available administrators:")
            rows = connection.execute(
                "SELECT username,display_name,active FROM users WHERE role='administrator' ORDER BY username"
            ).fetchall()
            for row in rows:
                print(f"- {row['username']} ({row['display_name']}, active={row['active']})")
            return 1

        token = secrets.token_urlsafe(32)
        token_id = f"AGQ-TEMPLOGIN-{secrets.token_hex(10).upper()}"
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(minutes=minutes)).isoformat(timespec="seconds")
        connection.execute(
            "INSERT INTO temporary_login_tokens(token_id,token_hash,user_id,expires_at,created_at) VALUES(?,?,?,?,?)",
            (
                token_id,
                hashlib.sha256(token.encode("utf-8")).hexdigest(),
                user["user_id"],
                expires_at,
                now.isoformat(timespec="seconds"),
            ),
        )
        connection.commit()
    finally:
        connection.close()

    base_url = args.base_url.rstrip("/")
    print()
    print("ONE-TIME AGROQ ADMINISTRATOR LINK")
    print(f"Expires: {expires_at}")
    print(f"Username: {args.username}")
    print()
    print(f"{base_url}/access/admin-link?token={token}")
    print()
    print("This link can be used once. Keep it private.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
