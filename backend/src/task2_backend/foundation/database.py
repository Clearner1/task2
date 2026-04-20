from __future__ import annotations

from contextlib import contextmanager
import sqlite3
from pathlib import Path
from typing import Iterator

from task2_backend.common.exceptions import DatabaseLockError


SCHEMA = """
CREATE TABLE IF NOT EXISTS media_files (
    media_id TEXT PRIMARY KEY,
    source_path TEXT NOT NULL UNIQUE,
    media_type TEXT NOT NULL,
    detected_format TEXT,
    duration_ms INTEGER,
    status TEXT NOT NULL,
    failure_reason TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS annotation_tasks (
    task_id TEXT PRIMARY KEY,
    media_id TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL,
    assigned_to TEXT,
    lock_owner TEXT,
    lock_acquired_at TEXT,
    lock_expires_at TEXT,
    submitted_at TEXT,
    reviewed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(media_id) REFERENCES media_files(media_id)
);

CREATE TABLE IF NOT EXISTS annotations (
    annotation_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    media_id TEXT NOT NULL,
    annotator_id TEXT NOT NULL,
    primary_emotion TEXT NOT NULL,
    secondary_emotions TEXT NOT NULL,
    intensity INTEGER NOT NULL,
    confidence INTEGER NOT NULL,
    valence REAL,
    arousal INTEGER,
    notes TEXT NOT NULL,
    is_draft INTEGER NOT NULL,
    version INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(task_id) REFERENCES annotation_tasks(task_id)
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL UNIQUE,
    reviewer_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    notes TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    FOREIGN KEY(task_id) REFERENCES annotation_tasks(task_id)
);

CREATE TABLE IF NOT EXISTS export_batches (
    batch_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    formats TEXT NOT NULL,
    output_paths TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS job_failures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_name TEXT NOT NULL,
    entity_id TEXT,
    failure_code TEXT NOT NULL,
    message TEXT NOT NULL,
    retry_count INTEGER NOT NULL,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    status TEXT NOT NULL DEFAULT 'pending',
    next_retry_at TEXT,
    payload_json TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL DEFAULT '',
    resolved_at TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS maintenance_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    summary_json TEXT NOT NULL DEFAULT '{}',
    error_message TEXT
);
"""


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=5.0, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except sqlite3.OperationalError as exc:
            connection.rollback()
            if "locked" in str(exc).lower():
                raise DatabaseLockError("Database is temporarily locked.") from exc
            raise
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def init_schema(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)
            self._ensure_column(connection, "job_failures", "max_attempts", "INTEGER NOT NULL DEFAULT 3")
            self._ensure_column(connection, "job_failures", "status", "TEXT NOT NULL DEFAULT 'pending'")
            self._ensure_column(connection, "job_failures", "next_retry_at", "TEXT")
            self._ensure_column(connection, "job_failures", "payload_json", "TEXT NOT NULL DEFAULT '{}'")
            self._ensure_column(connection, "job_failures", "updated_at", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection, "job_failures", "resolved_at", "TEXT")

    @staticmethod
    def _ensure_column(connection: sqlite3.Connection, table_name: str, column_name: str, definition: str) -> None:
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        if any(row["name"] == column_name for row in rows):
            return
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")
