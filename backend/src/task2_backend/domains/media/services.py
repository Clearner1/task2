from __future__ import annotations

from pathlib import Path
import logging
import json

from task2_backend.common.time import isoformat, now_utc
from task2_backend.domains.media.repository import MediaRepository
from task2_backend.domains.media.models import MediaAssetRecord, MediaRecord
from task2_backend.domains.media.schemas import MediaAssetItem, MediaImportResponse, MediaItem, MediaListResponse, MediaPreprocessResponse
from task2_backend.foundation.config import AppConfig
from task2_backend.foundation.operations import OperationsService
from task2_backend.foundation.media_normalizer import normalize_media
from task2_backend.foundation.media_probe import probe_media
from task2_backend.foundation.retry import run_with_retry

logger = logging.getLogger(__name__)


class MediaService:
    def __init__(
        self,
        config: AppConfig,
        repository: MediaRepository,
        operations_service: OperationsService | None = None,
    ):
        self.config = config
        self.repository = repository
        self.operations_service = operations_service

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
                self._preprocess_record(record)
                processed += 1
            except Exception as exc:
                logger.exception("Failed to preprocess media_id=%s", record.media_id)
                now_iso = isoformat(now_utc())
                self.repository.mark_failed(record.media_id, str(exc), now_iso)
                if self.operations_service is not None:
                    self.operations_service.record_job_failure(
                        "media_preprocess",
                        record.media_id,
                        exc,
                        payload={"media_id": record.media_id},
                        occurred_at=now_iso,
                    )
                failed += 1
        return MediaPreprocessResponse(processed=processed, failed=failed)

    def replay_preprocess_failure(self, media_id: str) -> None:
        record = self.repository.get_media(media_id)
        if record is None:
            raise ValueError(f"Media not found: {media_id}")
        if record.status.value == "PREPROCESSED":
            if self.operations_service is not None:
                self.operations_service.resolve_job_failure("media_preprocess", media_id)
            return
        self._preprocess_record(record)

    def _preprocess_record(self, record: MediaRecord) -> None:
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
        normalization = run_with_retry(
            "normalize_media",
            record.media_id,
            self.config.retry,
            lambda record=record, probe=probe: normalize_media(
                source_path=record.source_path,
                media_id=record.media_id,
                media_type=probe.media_type,
                config=self.config.media,
                normalized_root=self.config.paths.normalized_dir,
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
        for asset in [normalization.playable, normalization.waveform, normalization.poster]:
            if asset is None:
                continue
            self.repository.upsert_asset(
                record.media_id,
                asset.asset_kind,
                asset.path,
                asset.format,
                asset.sample_rate,
                asset.channels,
                asset.width,
                asset.height,
                updated_at,
                updated_at,
            )
        if normalization.waveform is None:
            self.repository.delete_asset(record.media_id, "waveform")
        if normalization.poster is None:
            self.repository.delete_asset(record.media_id, "poster")
        if self.operations_service is not None:
            self.operations_service.resolve_job_failure("media_preprocess", record.media_id, resolved_at=updated_at)

    def list_media(self, page: int, page_size: int, status: str | None) -> MediaListResponse:
        items, total = self.repository.list_media(page, page_size, status)
        return MediaListResponse(
            items=[self._to_media_item(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_media(self, media_id: str) -> MediaItem | None:
        item = self.repository.get_media(media_id)
        if item is None:
            return None
        return self._to_media_item(item)

    def get_stream_path(self, media_id: str) -> Path | None:
        record = self.repository.get_media(media_id)
        if record is None:
            return None
        playable = self._find_asset(record, "playable")
        return playable.path if playable is not None else record.source_path

    def get_poster_path(self, media_id: str) -> Path | None:
        record = self.repository.get_media(media_id)
        if record is None:
            return None
        poster = self._find_asset(record, "poster")
        return poster.path if poster is not None else None

    def get_waveform_payload(self, media_id: str) -> dict[str, object] | None:
        record = self.repository.get_media(media_id)
        if record is None:
            return None
        waveform = self._find_asset(record, "waveform")
        if waveform is None or not waveform.path.exists():
            return None
        return json.loads(waveform.path.read_text(encoding="utf-8"))

    def _infer_media_type(self, path: Path):
        from task2_backend.foundation.media_probe import infer_media_type

        return infer_media_type(
            path,
            self.config.media.supported_audio_extensions,
            self.config.media.supported_video_extensions,
        )

    def _to_media_item(self, item: MediaRecord) -> MediaItem:
        playable = self._find_asset(item, "playable")
        waveform = self._find_asset(item, "waveform")
        poster = self._find_asset(item, "poster")
        return MediaItem(
            media_id=item.media_id,
            source_path=str(item.source_path),
            media_type=item.media_type.value,
            detected_format=item.detected_format,
            duration_ms=item.duration_ms,
            status=item.status,
            failure_reason=item.failure_reason,
            stream_url=f"/api/media/{item.media_id}/stream",
            playable_asset_url=f"/api/media/{item.media_id}/stream" if playable is not None else None,
            waveform_url=f"/api/media/{item.media_id}/waveform" if waveform is not None else None,
            poster_url=f"/api/media/{item.media_id}/poster" if poster is not None else None,
            assets=[self._to_asset_item(item.media_id, asset) for asset in item.assets],
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    def _find_asset(item: MediaRecord, asset_kind: str) -> MediaAssetRecord | None:
        return next((asset for asset in item.assets if asset.asset_kind == asset_kind), None)

    @staticmethod
    def _to_asset_item(media_id: str, asset: MediaAssetRecord) -> MediaAssetItem:
        url_map = {
            "playable": f"/api/media/{media_id}/stream",
            "poster": f"/api/media/{media_id}/poster",
            "waveform": f"/api/media/{media_id}/waveform",
        }
        return MediaAssetItem(
            asset_kind=asset.asset_kind,
            path=str(asset.path),
            format=asset.format,
            sample_rate=asset.sample_rate,
            channels=asset.channels,
            width=asset.width,
            height=asset.height,
            url=url_map.get(asset.asset_kind, ""),
            created_at=asset.created_at,
            updated_at=asset.updated_at,
        )
