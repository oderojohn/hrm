"""Local SQLite storage for punches pulled from ZK devices — the "store them
locally" requirement, and the source of the pushed/unpushed watermark that
makes each push to the cloud incremental-only (only new punches get sent).
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from agent.config import get_db_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS punches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_name TEXT NOT NULL,
    device_user_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    raw_status INTEGER,
    pushed INTEGER NOT NULL DEFAULT 0,
    pushed_at TEXT,
    fetched_at TEXT NOT NULL,
    UNIQUE(device_name, device_user_id, timestamp)
);
CREATE INDEX IF NOT EXISTS idx_punches_pushed ON punches(pushed);
"""


@contextmanager
def get_connection():
    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def insert_punch(device_name, device_user_id, timestamp, raw_status):
    """Returns True if this punch was newly inserted, False if already known."""
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO punches (device_name, device_user_id, timestamp, raw_status, fetched_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (device_name, device_user_id, timestamp.isoformat(), raw_status, datetime.now(timezone.utc).isoformat()),
        )
        return cur.rowcount > 0


def get_unpushed_punches(device_name):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM punches WHERE device_name = ? AND pushed = 0 ORDER BY timestamp",
            (device_name,),
        ).fetchall()
        return [dict(r) for r in rows]


def mark_pushed(ids):
    if not ids:
        return
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.executemany("UPDATE punches SET pushed = 1, pushed_at = ? WHERE id = ?", [(now, i) for i in ids])


def count_unpushed():
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM punches WHERE pushed = 0").fetchone()
        return row["c"]


def count_total():
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM punches").fetchone()
        return row["c"]
