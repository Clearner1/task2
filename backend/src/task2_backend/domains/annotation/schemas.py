from __future__ import annotations

from pydantic import BaseModel, Field

from task2_backend.common.enums import TaskStatus


class AnnotationPayload(BaseModel):
    primary_emotion: str
    secondary_emotions: list[str] = Field(default_factory=list)
    intensity: int
    confidence: int
    valence: float | None = None
    arousal: int | None = None
    notes: str = ""


class AutosaveRequest(BaseModel):
    annotator_id: str
    annotation: AnnotationPayload


class SubmitRequest(BaseModel):
    annotator_id: str
    annotation: AnnotationPayload


class TaskLeaseRequest(BaseModel):
    annotator_id: str
    reason: str | None = None


class AnnotationView(BaseModel):
    annotation_id: str
    task_id: str
    media_id: str
    annotator_id: str
    annotation: AnnotationPayload
    is_draft: bool
    version: int
    created_at: str
    updated_at: str


class TaskItem(BaseModel):
    task_id: str
    media_id: str
    status: TaskStatus
    assigned_to: str | None = None
    lock_owner: str | None = None
    lock_expires_at: str | None = None
    submitted_at: str | None = None
    reviewed_at: str | None = None
    created_at: str
    updated_at: str


class TaskMediaAssetItem(BaseModel):
    asset_kind: str
    path: str
    format: str
    sample_rate: int | None = None
    channels: int | None = None
    width: int | None = None
    height: int | None = None
    url: str
    created_at: str
    updated_at: str


class TaskMediaItem(BaseModel):
    media_id: str
    source_path: str
    media_type: str
    detected_format: str | None = None
    duration_ms: int | None = None
    status: TaskStatus
    failure_reason: str | None = None
    stream_url: str
    playable_asset_url: str | None = None
    waveform_url: str | None = None
    poster_url: str | None = None
    assets: list[TaskMediaAssetItem] = Field(default_factory=list)
    created_at: str
    updated_at: str


class TaskDetail(BaseModel):
    task: TaskItem
    media: TaskMediaItem
    latest_draft: AnnotationView | None = None
    latest_annotation: AnnotationView | None = None


class TaskListResponse(BaseModel):
    items: list[TaskItem]
    total: int
    page: int
    page_size: int
