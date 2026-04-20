from __future__ import annotations

from datetime import timedelta
import json

from task2_backend.common.exceptions import AnnotationValidationError, NotFoundError
from task2_backend.common.time import isoformat, now_utc
from task2_backend.domains.annotation.repository import AnnotationRepository
from task2_backend.domains.annotation.schemas import (
    AnnotationPayload,
    AnnotationView,
    TaskDetail,
    TaskMediaAssetItem,
    TaskMediaItem,
    TaskItem,
    TaskListResponse,
)
from task2_backend.foundation.config import AppConfig


class AnnotationService:
    def __init__(self, config: AppConfig, repository: AnnotationRepository):
        self.config = config
        self.repository = repository

    def list_tasks(self, page: int, page_size: int, status: str | None, assigned_to: str | None) -> TaskListResponse:
        items, total = self.repository.list_tasks(page, page_size, status, assigned_to)
        return TaskListResponse(
            items=[
                TaskItem(
                    task_id=item.task_id,
                    media_id=item.media_id,
                    status=item.status,
                    assigned_to=item.assigned_to,
                    lock_owner=item.lock_owner,
                    lock_expires_at=item.lock_expires_at,
                    submitted_at=item.submitted_at,
                    reviewed_at=item.reviewed_at,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
                for item in items
            ],
            total=total,
            page=page,
            page_size=page_size,
        )

    def sync_from_media(self) -> None:
        now_iso = isoformat(now_utc())
        self.repository.sync_tasks_from_media(now_iso)
        self.repository.sync_ready_tasks(now_iso)

    def acquire_next_task(self, annotator_id: str) -> TaskDetail | None:
        now_iso = isoformat(now_utc())
        task = self.repository.acquire_next_task(
            annotator_id,
            now_iso,
            self.config.annotation.task_lock_timeout_seconds,
        )
        if task is None:
            return None
        return self.get_task_detail(task.task_id)

    def get_task_detail(self, task_id: str) -> TaskDetail:
        row = self.repository.get_task_media_row(task_id)
        if row is None:
            raise NotFoundError(f"Task not found: {task_id}", entity_id=task_id)
        asset_rows = self.repository.list_media_assets(row["media_id"])
        latest_draft_row = self.repository.get_latest_annotation(task_id, is_draft=True)
        latest_annotation_row = self.repository.get_latest_annotation(task_id)
        latest_draft = self._build_annotation_view(latest_draft_row) if latest_draft_row else None
        latest_annotation = self._build_annotation_view(latest_annotation_row) if latest_annotation_row else None
        compat_latest_draft = latest_draft or latest_annotation
        if row["status"] in {"SUBMITTED", "REVIEWED", "EXPORTED"}:
            compat_latest_draft = latest_annotation
        assets = [self._build_media_asset_item(row["media_id"], asset_row) for asset_row in asset_rows]
        playable_asset = next((asset for asset in assets if asset.asset_kind == "playable"), None)
        waveform_asset = next((asset for asset in assets if asset.asset_kind == "waveform"), None)
        poster_asset = next((asset for asset in assets if asset.asset_kind == "poster"), None)
        return TaskDetail(
            task=TaskItem(
                task_id=row["task_id"],
                media_id=row["media_id"],
                status=row["status"],
                assigned_to=row["assigned_to"],
                lock_owner=row["lock_owner"],
                lock_expires_at=row["lock_expires_at"],
                submitted_at=row["submitted_at"],
                reviewed_at=row["reviewed_at"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            ),
            media=TaskMediaItem(
                media_id=row["media_id"],
                source_path=row["source_path"],
                media_type=row["media_type"],
                detected_format=row["detected_format"],
                duration_ms=row["duration_ms"],
                status=row["media_status"],
                failure_reason=row["failure_reason"],
                stream_url=f"/api/media/{row['media_id']}/stream",
                playable_asset_url=playable_asset.url if playable_asset else None,
                waveform_url=waveform_asset.url if waveform_asset else None,
                poster_url=poster_asset.url if poster_asset else None,
                assets=assets,
                created_at=row["media_created_at"],
                updated_at=row["media_updated_at"],
            ),
            latest_draft=compat_latest_draft,
            latest_annotation=latest_annotation,
        )

    def autosave(self, task_id: str, annotator_id: str, annotation: AnnotationPayload) -> TaskDetail:
        task = self.repository.get_task(task_id)
        if task is None:
            raise NotFoundError(f"Task not found: {task_id}", entity_id=task_id)
        payload = self._validate_annotation(annotation)
        now = now_utc()
        self.repository.create_annotation(
            task_id,
            task.media_id,
            annotator_id,
            payload,
            True,
            isoformat(now),
            isoformat(now + timedelta(seconds=self.config.annotation.task_lock_timeout_seconds)),
        )
        return self.get_task_detail(task_id)

    def heartbeat(self, task_id: str, annotator_id: str) -> TaskDetail:
        task = self.repository.get_task(task_id)
        if task is None:
            raise NotFoundError(f"Task not found: {task_id}", entity_id=task_id)
        now = now_utc()
        self.repository.heartbeat_task(
            task_id,
            annotator_id,
            isoformat(now + timedelta(seconds=self.config.annotation.task_lock_timeout_seconds)),
            isoformat(now),
        )
        return self.get_task_detail(task_id)

    def submit(self, task_id: str, annotator_id: str, annotation: AnnotationPayload) -> TaskDetail:
        task = self.repository.get_task(task_id)
        if task is None:
            raise NotFoundError(f"Task not found: {task_id}", entity_id=task_id)
        payload = self._validate_annotation(annotation)
        self.repository.create_annotation(
            task_id,
            task.media_id,
            annotator_id,
            payload,
            False,
            isoformat(now_utc()),
            None,
        )
        return self.get_task_detail(task_id)

    def release(self, task_id: str, annotator_id: str) -> TaskDetail:
        task = self.repository.get_task(task_id)
        if task is None:
            raise NotFoundError(f"Task not found: {task_id}", entity_id=task_id)
        self.repository.release_task(task_id, annotator_id, isoformat(now_utc()))
        return self.get_task_detail(task_id)

    def reclaim_expired_locks(self) -> int:
        reclaimed = self.repository.reclaim_expired_tasks(isoformat(now_utc()))
        return len(reclaimed)

    def _validate_annotation(self, annotation: AnnotationPayload) -> dict[str, object]:
        payload = annotation.model_dump()
        if payload["primary_emotion"] not in self.config.annotation.allowed_primary_labels:
            raise AnnotationValidationError(
                f"Unsupported primary emotion: {payload['primary_emotion']}"
            )
        if not 1 <= int(payload["intensity"]) <= 5:
            raise AnnotationValidationError("Intensity must be between 1 and 5.")
        if not 1 <= int(payload["confidence"]) <= 5:
            raise AnnotationValidationError("Confidence must be between 1 and 5.")
        if payload["valence"] is not None and not -1 <= float(payload["valence"]) <= 1:
            raise AnnotationValidationError("Valence must be between -1 and 1.")
        if payload["arousal"] is not None and not 1 <= int(payload["arousal"]) <= 5:
            raise AnnotationValidationError("Arousal must be between 1 and 5.")
        return payload

    @staticmethod
    def _build_annotation_view(row) -> AnnotationView:
        return AnnotationView(
            annotation_id=row["annotation_id"],
            task_id=row["task_id"],
            media_id=row["media_id"],
            annotator_id=row["annotator_id"],
            annotation=AnnotationPayload(
                primary_emotion=row["primary_emotion"],
                secondary_emotions=json.loads(row["secondary_emotions"]),
                intensity=row["intensity"],
                confidence=row["confidence"],
                valence=row["valence"],
                arousal=row["arousal"],
                notes=row["notes"],
            ),
            is_draft=bool(row["is_draft"]),
            version=row["version"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _build_media_asset_item(media_id: str, row) -> TaskMediaAssetItem:
        url_map = {
            "playable": f"/api/media/{media_id}/stream",
            "waveform": f"/api/media/{media_id}/waveform",
            "poster": f"/api/media/{media_id}/poster",
        }
        return TaskMediaAssetItem(
            asset_kind=row["asset_kind"],
            path=row["path"],
            format=row["format"],
            sample_rate=row["sample_rate"],
            channels=row["channels"],
            width=row["width"],
            height=row["height"],
            url=url_map.get(row["asset_kind"], ""),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
