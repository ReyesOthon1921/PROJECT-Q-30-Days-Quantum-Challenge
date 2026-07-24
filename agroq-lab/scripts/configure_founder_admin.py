from __future__ import annotations

import argparse
from datetime import datetime, timezone
from getpass import getpass
import os
from pathlib import Path
import sqlite3
import time
from typing import Any

from werkzeug.security import generate_password_hash


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = Path(
    os.environ.get(
        "AGROQ_DB_PATH",
        BASE_DIR / "instance" / "agroq.db",
    )
)


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
        is not None
    )


def table_columns(
    conn: sqlite3.Connection,
    table_name: str,
) -> dict[str, sqlite3.Row]:
    return {
        row["name"]: row
        for row in conn.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()
    }


def default_required_value(
    column_name: str,
    column_type: str,
    *,
    display_name: str,
    email: str,
    now: str,
) -> Any:
    name = column_name.lower()
    declared_type = (column_type or "").upper()

    explicit_values: dict[str, Any] = {
        "created_at": now,
        "updated_at": now,
        "email": email,
        "display_name": display_name,
        "relationship_type": "contributor",
        "relationship": "contributor",
        "organization": "AgroQ",
        "title": "Founder, CEO and Principal Systems Architect",
        "privacy_level": "private",
        "bio": "",
        "github_url": "",
        "linkedin_url": "",
        "contact_consent": 1,
        "active": 1,
    }
    if name in explicit_values:
        return explicit_values[name]

    if "INT" in declared_type:
        return 0
    if any(token in declared_type for token in ("REAL", "FLOA", "DOUB", "NUM")):
        return 0.0
    return ""


def upsert_profile(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    display_name: str,
    email: str,
    now: str,
) -> None:
    if not table_exists(conn, "user_profiles"):
        return

    columns = table_columns(conn, "user_profiles")
    existing = conn.execute(
        "SELECT * FROM user_profiles WHERE user_id=?",
        (user_id,),
    ).fetchone()

    known_values: dict[str, Any] = {
        "email": email,
        "display_name": display_name,
        "organization": "AgroQ",
        "title": "Founder, CEO and Principal Systems Architect",
        "privacy_level": "private",
        "updated_at": now,
    }

    if existing is not None:
        updates = {
            key: value
            for key, value in known_values.items()
            if key in columns
        }
        if updates:
            assignments = ", ".join(
                f"{column}=?" for column in updates
            )
            conn.execute(
                f"UPDATE user_profiles SET {assignments} WHERE user_id=?",
                (*updates.values(), user_id),
            )
        return

    insert_values: dict[str, Any] = {"user_id": user_id}

    for key, value in known_values.items():
        if key in columns:
            insert_values[key] = value

    if "created_at" in columns:
        insert_values["created_at"] = now

    for column_name, metadata in columns.items():
        if column_name in insert_values:
            continue
        if metadata["pk"]:
            continue

        is_required = bool(metadata["notnull"])
        has_default = metadata["dflt_value"] is not None
        if is_required and not has_default:
            insert_values[column_name] = default_required_value(
                column_name,
                metadata["type"],
                display_name=display_name,
                email=email,
                now=now,
            )

    names = ", ".join(insert_values)
    placeholders = ", ".join("?" for _ in insert_values)

    conn.execute(
        f"INSERT INTO user_profiles({names}) VALUES({placeholders})",
        tuple(insert_values.values()),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create or update the AgroQ founder administrator account."
    )
    parser.add_argument("--username", default="admin")
    parser.add_argument("--display-name", default="Othon Reyes Jr.")
    parser.add_argument("--email", default="reyesothon1921@gmail.com")
    parser.add_argument(
        "--keep-password",
        action="store_true",
        help="Preserve the current password hash for an existing account.",
    )
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        print("Start AgroQ once with python app.py, stop it, and rerun.")
        return 1

    password_hash: str | None = None
    if not args.keep_password:
        password = getpass("Administrator password: ")
        confirmation = getpass("Confirm administrator password: ")

        if len(password) < 12:
            print("Use a password with at least 12 characters.")
            return 1
        if password != confirmation:
            print("Passwords did not match.")
            return 1

        password_hash = generate_password_hash(password)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        with conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username=?",
                (args.username,),
            ).fetchone()

            now = datetime.now(timezone.utc).isoformat(
                timespec="seconds"
            )

            if row is None:
                if password_hash is None:
                    print(
                        "--keep-password cannot create a new account "
                        "because no existing password is available."
                    )
                    return 1

                user_id = f"AGQ-ADMIN-{time.time_ns()}"
                site = conn.execute(
                    "SELECT site_id FROM sites ORDER BY created_at LIMIT 1"
                ).fetchone()
                site_id = site["site_id"] if site else None

                conn.execute(
                    "INSERT INTO users("
                    "user_id, username, display_name, password_hash, "
                    "role, site_id, active, created_at"
                    ") VALUES(?,?,?,?,?,?,1,?)",
                    (
                        user_id,
                        args.username,
                        args.display_name,
                        password_hash,
                        "administrator",
                        site_id,
                        now,
                    ),
                )
            else:
                user_id = row["user_id"]

                if password_hash is None:
                    conn.execute(
                        "UPDATE users "
                        "SET display_name=?, role='administrator', active=1 "
                        "WHERE user_id=?",
                        (args.display_name, user_id),
                    )
                else:
                    conn.execute(
                        "UPDATE users "
                        "SET display_name=?, password_hash=?, "
                        "role='administrator', active=1 "
                        "WHERE user_id=?",
                        (
                            args.display_name,
                            password_hash,
                            user_id,
                        ),
                    )

            upsert_profile(
                conn,
                user_id=user_id,
                display_name=args.display_name,
                email=args.email,
                now=now,
            )

        print("Founder administrator configured.")
        print(f"Username: {args.username}")
        print(f"Display name: {args.display_name}")
        print(f"Email: {args.email}")
        print("Role: administrator")
        print("Active: yes")
        if args.keep_password:
            print("Password preserved: yes")
        else:
            print("Password updated: yes")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
