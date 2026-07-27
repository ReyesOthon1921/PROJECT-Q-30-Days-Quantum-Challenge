from contextlib import contextmanager
import sqlite3
from pathlib import Path
from notification_center import initialize_notification_schema

BASE_DIR=Path(__file__).resolve().parents[1]

@contextmanager
def db_connection(path):
    conn=sqlite3.connect(path); conn.row_factory=sqlite3.Row; conn.execute("PRAGMA foreign_keys = ON")
    try:
        with conn: yield conn
    finally: conn.close()

def initialize_base(path):
    with db_connection(path) as conn:
        conn.executescript((BASE_DIR/"schema.sql").read_text(encoding="utf-8"))

def test_notification_schema_tracks_the_actual_database(tmp_path):
    for name in ("first.db","second.db"):
        path=tmp_path/name; initialize_base(path)
        initialize_notification_schema(lambda path=path: db_connection(path))
        with db_connection(path) as conn:
            assert conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='admin_notification_events'").fetchone()
