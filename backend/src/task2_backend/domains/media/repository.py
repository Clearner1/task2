from __future__ import annotations

from pathlib import Path
import sqlite3

from task2_backend.common.enums import MediaType, TaskStatus
from task2_backend.domains.media.models import MediaAssetRecord, MediaRecord
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
            asset_map = self._list_assets_by_media_ids(connection, [str(row["media_id"]) for row in rows])
        return [self._from_row(row, asset_map.get(str(row["media_id"]), ())) for row in rows], int(total)

    def get_media(self, media_id: str) -> MediaRecord | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM media_files WHERE media_id = ?",
                [media_id],
            ).fetchone()
            assets = self._list_assets_by_media_ids(connection, [media_id]).get(media_id, ())
        return self._from_row(row, assets) if row else None

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
                """
                SELECT m.*
                FROM media_files m
                LEFT JOIN media_assets playable
                    ON playable.media_id = m.media_id AND playable.asset_kind = 'playable'
                WHERE m.status = ?
                   OR (m.status = ? AND playable.id IS NULL)
                   OR m.failure_reason IS NOT NULL
                ORDER BY m.created_at ASC
                """,
                [TaskStatus.IMPORTED.value, TaskStatus.PREPROCESSED.value],
            ).fetchall()
            asset_map = self._list_assets_by_media_ids(connection, [str(row["media_id"]) for row in rows])
        return [self._from_row(row, asset_map.get(str(row["media_id"]), ())) for row in rows]

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

    def upsert_asset(
        self,
        media_id: str,
        asset_kind: str,
        path: Path,
        format_name: str,
        sample_rate: int | None,
        channels: int | None,
        width: int | None,
        height: int | None,
        created_at: str,
        updated_at: str,
    ) -> None:
        with self.database.connect() as connection:
            existing = connection.execute(
                "SELECT id, created_at FROM media_assets WHERE media_id = ? AND asset_kind = ?",
                [media_id, asset_kind],
            ).fetchone()
            if existing is None:
                connection.execute(
                    """
                    INSERT INTO media_assets (
                        media_id, asset_kind, path, format, sample_rate, channels, width, height, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        media_id,
                        asset_kind,
                        str(path),
                        format_name,
                        sample_rate,
                        channels,
                        width,
                        height,
                        created_at,
                        updated_at,
                    ],
                )
                return
            connection.execute(
                """
                UPDATE media_assets
                SET path = ?, format = ?, sample_rate = ?, channels = ?, width = ?, height = ?, updated_at = ?
                WHERE id = ?
                """,
                [str(path), format_name, sample_rate, channels, width, height, updated_at, existing["id"]],
            )

    def delete_asset(self, media_id: str, asset_kind: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "DELETE FROM media_assets WHERE media_id = ? AND asset_kind = ?",
                [media_id, asset_kind],
            )

    @staticmethod
    def _list_assets_by_media_ids(connection: sqlite3.Connection, media_ids: list[str]) -> dict[str, tuple[MediaAssetRecord, ...]]:
        if not media_ids:
            return {}
        placeholders = ",".join("?" for _ in media_ids)
        rows = connection.execute(
            f"""
            SELECT *
            FROM media_assets
            WHERE media_id IN ({placeholders})
            ORDER BY asset_kind ASC, created_at ASC
            """,
            media_ids,
        ).fetchall()
        grouped: dict[str, list[MediaAssetRecord]] = {}
        for row in rows:
            grouped.setdefault(str(row["media_id"]), []).append(MediaRepository._asset_from_row(row))
        return {media_id: tuple(items) for media_id, items in grouped.items()}

    @staticmethod
    def _from_row(row: sqlite3.Row, assets: tuple[MediaAssetRecord, ...]) -> MediaRecord:
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
            assets=assets,
        )

    @staticmethod
    def _asset_from_row(row: sqlite3.Row) -> MediaAssetRecord:
        return MediaAssetRecord(
            media_id=row["media_id"],
            asset_kind=row["asset_kind"],
            path=Path(row["path"]),
            format=row["format"],
            sample_rate=row["sample_rate"],
            channels=row["channels"],
            width=row["width"],
            height=row["height"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
