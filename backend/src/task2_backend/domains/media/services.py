from __future__ import annotations

from pathlib import Path
import logging

from task2_backend.common.time import isoformat, now_utc
from task2_backend.domains.media.repository import MediaRepository
from task2_backend.domains.media.schemas import MediaImportResponse, MediaItem, MediaListResponse, MediaPreprocessResponse
from task2_backend.foundation.config import AppConfig
from task2_backend.foundation.media_probe import probe_media
from task2_backend.foundation.retry import run_with_retry

logger = logging.getLogger(__name__)


class MediaService:
    def __init__(
        self,
        config: AppConfig,
        repository: MediaRepository,
    ):
        self.config = config
        self.repository = repository

    def import_media(self) -> MediaImportResponse:
        imported = 0
        existing = 0
        for path in sorted(self.config.paths.input_dir.iterdir()):
            if path.name.startswith(".") or not path.is_file():
                continue
            media_id = path.stem
            created_at = isoformat(now_utc())
            media_type = self._infer_media_type(path)
            if self.repository.register_media(media_id, path.resolve(), media_type, created_at):
                imported += 1
            else:
                existing += 1
        return MediaImportResponse(imported=imported, existing=existing)

    def preprocess_media(self) -> MediaPreprocessResponse:
        processed = 0
        failed = 0
        for record in self.repository.list_pending_preprocess():
            try:
                probe = run_with_retry(
                    "probe_media",
                    record.media_id,
                    self.config.retry,
                    lambda record=record: probe_media(
                        record.source_path,
                        self.config.media.supported_audio_extensions,
                        self.config.media.supported_video_extensions,
                    ),
                )
                updated_at = isoformat(now_utc())
                self.repository.mark_preprocessed(
                    record.media_id,
                    probe.media_type,
                    probe.detected_format,
                    probe.duration_ms,
                    updated_at,
                )
                processed += 1
            except Exception as exc:
                logger.exception("Failed to preprocess media_id=%s", record.media_id)
                self.repository.mark_failed(record.media_id, str(exc), isoformat(now_utc()))
                failed += 1
        return MediaPreprocessResponse(processed=processed, failed=failed)

    def list_media(self, page: int, page_size: int, status: str | None) -> MediaListResponse:
        items, total = self.repository.list_media(page, page_size, status)
        return MediaListResponse(
            items=[
                MediaItem(
                    media_id=item.media_id,
                    source_path=str(item.source_path),
                    media_type=item.media_type.value,
                    detected_format=item.detected_format,
                    duration_ms=item.duration_ms,
                    status=item.status,
                    failure_reason=item.failure_reason,
                    stream_url=f"/api/media/{item.media_id}/stream",
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
                for item in items
            ],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_media(self, media_id: str) -> MediaItem | None:
        item = self.repository.get_media(media_id)
        if item is None:
            return None
        return MediaItem(
            media_id=item.media_id,
            source_path=str(item.source_path),
            media_type=item.media_type.value,
            detected_format=item.detected_format,
            duration_ms=item.duration_ms,
            status=item.status,
            failure_reason=item.failure_reason,
            stream_url=f"/api/media/{item.media_id}/stream",
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def get_stream_path(self, media_id: str) -> Path | None:
        record = self.repository.get_media(media_id)
        return record.source_path if record else None

    def _infer_media_type(self, path: Path):
        from task2_backend.foundation.media_probe import infer_media_type

        return infer_media_type(
            path,
            self.config.media.supported_audio_extensions,
            self.config.media.supported_video_extensions,
        )
