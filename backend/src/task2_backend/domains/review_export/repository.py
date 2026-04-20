from __future__ import annotations

import sqlite3
from uuid import uuid4

from task2_backend.common.enums import ExportStatus, TaskStatus
from task2_backend.domains.review_export.models import ExportBatchRecord
from task2_backend.foundation.database import Database


class ReviewExportRepository:
    def __init__(self, database: Database):
        self.database = database

    def save_review(self, task_id: str, reviewer_id: str, decision: str, notes: str, reviewed_at: str) -> None:
        with self.database.connect() as connection:
            existing = connection.execute(
                "SELECT review_id FROM reviews WHERE task_id = ?",
                [task_id],
            ).fetchone()
            if existing:
                connection.execute(
                    """
                    UPDATE reviews
                    SET reviewer_id = ?, decision = ?, notes = ?, reviewed_at = ?
                    WHERE task_id = ?
                    """,
                    [reviewer_id, decision, notes, reviewed_at, task_id],
                )
            else:
                connection.execute(
                    """
                    INSERT INTO reviews (review_id, task_id, reviewer_id, decision, notes, reviewed_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [str(uuid4()), task_id, reviewer_id, decision, notes, reviewed_at],
                )
            connection.execute(
                """
                UPDATE annotation_tasks
                SET status = ?, reviewed_at = ?, updated_at = ?
                WHERE task_id = ?
                """,
                [TaskStatus.REVIEWED.value, reviewed_at, reviewed_at, task_id],
            )

    def create_export_batch(self, formats: list[str], output_paths: list[str], created_at: str) -> ExportBatchRecord:
        batch_id = str(uuid4())
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO export_batches (batch_id, status, formats, output_paths, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                [batch_id, ExportStatus.SUCCESS.value, ",".join(formats), "\n".join(output_paths), created_at],
            )
            connection.execute(
                """
                UPDATE annotation_tasks
                SET status = ?, updated_at = ?
                WHERE status = ?
                """,
                [TaskStatus.EXPORTED.value, created_at, TaskStatus.REVIEWED.value],
            )
        return ExportBatchRecord(
            batch_id=batch_id,
            status=ExportStatus.SUCCESS.value,
            formats=",".join(formats),
            output_paths="\n".join(output_paths),
            created_at=created_at,
        )

    def get_export_batch(self, batch_id: str) -> ExportBatchRecord | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM export_batches WHERE batch_id = ?",
                [batch_id],
            ).fetchone()
        if row is None:
            return None
        return ExportBatchRecord(
            batch_id=row["batch_id"],
            status=row["status"],
            formats=row["formats"],
            output_paths=row["output_paths"],
            created_at=row["created_at"],
        )

    def get_export_rows(self) -> list[sqlite3.Row]:
        with self.database.connect() as connection:
            return connection.execute(
                """
                SELECT
                    t.task_id,
                    t.media_id,
                    t.submitted_at,
                    m.source_path,
                    m.media_type,
                    m.detected_format,
                    m.duration_ms,
                    a.annotator_id,
                    a.primary_emotion,
                    a.secondary_emotions,
                    a.intensity,
                    a.confidence,
                    a.valence,
                    a.arousal,
                    a.notes,
                    r.decision,
                    r.reviewer_id,
                    r.reviewed_at
                FROM annotation_tasks t
                JOIN media_files m ON m.media_id = t.media_id
                JOIN annotations a ON a.task_id = t.task_id
                JOIN reviews r ON r.task_id = t.task_id
                WHERE t.status = ? AND a.is_draft = 0 AND a.version = (
                    SELECT MAX(version) FROM annotations latest WHERE latest.task_id = t.task_id AND latest.is_draft = 0
                )
                ORDER BY t.created_at ASC
                """,
                [TaskStatus.REVIEWED.value],
            ).fetchall()
