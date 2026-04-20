from __future__ import annotations

from pathlib import Path
import sqlite3

from task2_backend.common.enums import MediaType, TaskStatus
from task2_backend.domains.media.models import MediaRecord
from task2_backend.foundation.database import Database


class MediaRepository:
    def __init__(self, database: Database):
        self.database = database

    def list_media(self, page: int, page_size: int, status: str | None) -> tuple[list[MediaRecord], int]:
        offset = (page - 1) * page_size
        query = "SELECT * FROM media_files"
        count_query = "SELECT COUNT(*) AS count FROM media_files"
        params: list[object] = []
        if status:
            query += " WHERE status = ?"
            count_query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY created_at ASC LIMIT ? OFFSET ?"
        with self.database.connect() as connection:
            total = connection.execute(count_query, params).fetchone()["count"]
            rows = connection.execute(query, [*params, page_size, offset]).fetchall()
        return [self._from_row(row) for row in rows], int(total)

    def get_media(self, media_id: str) -> MediaRecord | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM media_files WHERE media_id = ?",
                [media_id],
            ).fetchone()
        return self._from_row(row) if row else None

    def register_media(
        self,
        media_id: str,
        source_path: Path,
        media_type: MediaType,
        created_at: str,
    ) -> bool:
        with self.database.connect() as connection:
            existing = connection.execute(
                "SELECT media_id FROM media_files WHERE media_id = ? OR source_path = ?",
                [media_id, str(source_path)],
            ).fetchone()
            if existing:
                return False
            connection.execute(
                """
                INSERT INTO media_files (
                    media_id, source_path, media_type, detected_format, duration_ms,
                    status, failure_reason, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    media_id,
                    str(source_path),
                    media_type.value,
                    None,
                    None,
                    TaskStatus.IMPORTED.value,
                    None,
                    created_at,
                    created_at,
                ],
            )
        return True

    def list_pending_preprocess(self) -> list[MediaRecord]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM media_files WHERE status = ? ORDER BY created_at ASC",
                [TaskStatus.IMPORTED.value],
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def mark_preprocessed(
        self,
        media_id: str,
        media_type: MediaType,
        detected_format: str,
        duration_ms: int,
        updated_at: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE media_files
                SET media_type = ?, detected_format = ?, duration_ms = ?, status = ?, failure_reason = ?, updated_at = ?
                WHERE media_id = ?
                """,
                [
                    media_type.value,
                    detected_format,
                    duration_ms,
                    TaskStatus.PREPROCESSED.value,
                    None,
                    updated_at,
                    media_id,
                ],
            )

    def mark_failed(self, media_id: str, reason: str, updated_at: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "UPDATE media_files SET failure_reason = ?, updated_at = ? WHERE media_id = ?",
                [reason, updated_at, media_id],
            )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> MediaRecord:
        return MediaRecord(
            media_id=row["media_id"],
            source_path=Path(row["source_path"]),
            media_type=MediaType(row["media_type"]),
            detected_format=row["detected_format"],
            duration_ms=row["duration_ms"],
            status=TaskStatus(row["status"]),
            failure_reason=row["failure_reason"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
