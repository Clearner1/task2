from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import sqlite3
from uuid import uuid4

from task2_backend.common.enums import TaskStatus
from task2_backend.domains.annotation.models import TaskRecord
from task2_backend.foundation.database import Database


class AnnotationRepository:
    def __init__(self, database: Database):
        self.database = database

    def ensure_task(self, media_id: str, created_at: str) -> None:
        with self.database.connect() as connection:
            existing = connection.execute(
                "SELECT task_id FROM annotation_tasks WHERE media_id = ?",
                [media_id],
            ).fetchone()
            if existing:
                return
            connection.execute(
                """
                INSERT INTO annotation_tasks (
                    task_id, media_id, status, assigned_to, lock_owner, lock_acquired_at,
                    lock_expires_at, submitted_at, reviewed_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    str(uuid4()),
                    media_id,
                    TaskStatus.IMPORTED.value,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    created_at,
                    created_at,
                ],
            )

    def sync_tasks_from_media(self, created_at: str) -> None:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT media_id
                FROM media_files
                WHERE media_id NOT IN (SELECT media_id FROM annotation_tasks)
                """
            ).fetchall()
        for row in rows:
            self.ensure_task(row["media_id"], created_at)

    def mark_task_ready(self, media_id: str, updated_at: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE annotation_tasks
                SET status = ?, updated_at = ?
                WHERE media_id = ? AND status IN (?, ?)
                """,
                [
                    TaskStatus.READY.value,
                    updated_at,
                    media_id,
                    TaskStatus.IMPORTED.value,
                    TaskStatus.PREPROCESSED.value,
                ],
            )

    def sync_ready_tasks(self, updated_at: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE annotation_tasks
                SET status = ?, updated_at = ?
                WHERE media_id IN (
                    SELECT media_id FROM media_files WHERE status = ?
                )
                AND status IN (?, ?)
                """,
                [
                    TaskStatus.READY.value,
                    updated_at,
                    TaskStatus.PREPROCESSED.value,
                    TaskStatus.IMPORTED.value,
                    TaskStatus.PREPROCESSED.value,
                ],
            )

    def list_tasks(self, page: int, page_size: int, status: str | None, assigned_to: str | None) -> tuple[list[TaskRecord], int]:
        offset = (page - 1) * page_size
        filters: list[str] = []
        params: list[object] = []
        if status:
            filters.append("status = ?")
            params.append(status)
        if assigned_to:
            filters.append("assigned_to = ?")
            params.append(assigned_to)
        where_clause = f" WHERE {' AND '.join(filters)}" if filters else ""
        query = f"SELECT * FROM annotation_tasks{where_clause} ORDER BY created_at ASC LIMIT ? OFFSET ?"
        count_query = f"SELECT COUNT(*) AS count FROM annotation_tasks{where_clause}"
        with self.database.connect() as connection:
            total = connection.execute(count_query, params).fetchone()["count"]
            rows = connection.execute(query, [*params, page_size, offset]).fetchall()
        return [self._from_row(row) for row in rows], int(total)

    def get_task(self, task_id: str) -> TaskRecord | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM annotation_tasks WHERE task_id = ?",
                [task_id],
            ).fetchone()
        return self._from_row(row) if row else None

    def acquire_next_task(self, annotator_id: str, now_iso: str, timeout_seconds: int) -> TaskRecord | None:
        now_dt = datetime.fromisoformat(now_iso)
        expires_at = now_dt + timedelta(seconds=timeout_seconds)
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM annotation_tasks
                WHERE status = ?
                   OR (status = ? AND lock_expires_at IS NOT NULL AND lock_expires_at < ?)
                ORDER BY created_at ASC
                LIMIT 1
                """,
                [TaskStatus.READY.value, TaskStatus.IN_PROGRESS.value, now_iso],
            ).fetchone()
            if not row:
                return None
            connection.execute(
                """
                UPDATE annotation_tasks
                SET status = ?, assigned_to = ?, lock_owner = ?, lock_acquired_at = ?, lock_expires_at = ?, updated_at = ?
                WHERE task_id = ?
                """,
                [
                    TaskStatus.IN_PROGRESS.value,
                    annotator_id,
                    annotator_id,
                    now_iso,
                    expires_at.isoformat(),
                    now_iso,
                    row["task_id"],
                ],
            )
            refreshed = connection.execute(
                "SELECT * FROM annotation_tasks WHERE task_id = ?",
                [row["task_id"]],
            ).fetchone()
        return self._from_row(refreshed) if refreshed else None

    def create_annotation(
        self,
        task_id: str,
        media_id: str,
        annotator_id: str,
        payload: dict[str, object],
        is_draft: bool,
        now_iso: str,
        lock_expires_at: str | None,
    ) -> None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT COALESCE(MAX(version), 0) AS version FROM annotations WHERE task_id = ?",
                [task_id],
            ).fetchone()
            version = int(row["version"]) + 1
            connection.execute(
                """
                INSERT INTO annotations (
                    annotation_id, task_id, media_id, annotator_id, primary_emotion, secondary_emotions,
                    intensity, confidence, valence, arousal, notes, is_draft, version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    str(uuid4()),
                    task_id,
                    media_id,
                    annotator_id,
                    payload["primary_emotion"],
                    json.dumps(payload.get("secondary_emotions", []), ensure_ascii=False),
                    payload["intensity"],
                    payload["confidence"],
                    payload.get("valence"),
                    payload.get("arousal"),
                    payload.get("notes", ""),
                    1 if is_draft else 0,
                    version,
                    now_iso,
                    now_iso,
                ],
            )
            connection.execute(
                """
                UPDATE annotation_tasks
                SET status = ?, assigned_to = ?, lock_owner = ?, lock_acquired_at = ?, lock_expires_at = ?, submitted_at = ?, updated_at = ?
                WHERE task_id = ?
                """,
                [
                    TaskStatus.IN_PROGRESS.value if is_draft else TaskStatus.SUBMITTED.value,
                    annotator_id,
                    annotator_id if is_draft else None,
                    now_iso if is_draft else None,
                    lock_expires_at if is_draft else None,
                    None if is_draft else now_iso,
                    now_iso,
                    task_id,
                ],
            )

    def get_latest_annotation(self, task_id: str, is_draft: bool | None = None) -> sqlite3.Row | None:
        clause = ""
        params: list[object] = [task_id]
        if is_draft is not None:
            clause = " AND is_draft = ?"
            params.append(1 if is_draft else 0)
        with self.database.connect() as connection:
            return connection.execute(
                f"""
                SELECT * FROM annotations
                WHERE task_id = ?{clause}
                ORDER BY version DESC
                LIMIT 1
                """,
                params,
            ).fetchone()

    def get_task_media_row(self, task_id: str) -> sqlite3.Row | None:
        with self.database.connect() as connection:
            return connection.execute(
                """
                SELECT
                    t.*,
                    m.source_path,
                    m.media_type,
                    m.detected_format,
                    m.duration_ms,
                    m.status AS media_status,
                    m.failure_reason,
                    m.created_at AS media_created_at,
                    m.updated_at AS media_updated_at
                FROM annotation_tasks t
                JOIN media_files m ON t.media_id = m.media_id
                WHERE t.task_id = ?
                """,
                [task_id],
            ).fetchone()

    @staticmethod
    def _from_row(row: sqlite3.Row) -> TaskRecord:
        return TaskRecord(
            task_id=row["task_id"],
            media_id=row["media_id"],
            status=TaskStatus(row["status"]),
            assigned_to=row["assigned_to"],
            lock_owner=row["lock_owner"],
            lock_acquired_at=row["lock_acquired_at"],
            lock_expires_at=row["lock_expires_at"],
            submitted_at=row["submitted_at"],
            reviewed_at=row["reviewed_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
