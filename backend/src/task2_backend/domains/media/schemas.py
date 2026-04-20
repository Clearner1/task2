from __future__ import annotations

from pydantic import BaseModel

from task2_backend.common.enums import TaskStatus


class MediaItem(BaseModel):
    media_id: str
    source_path: str
    media_type: str
    detected_format: str | None = None
    duration_ms: int | None = None
    status: TaskStatus
    failure_reason: str | None = None
    stream_url: str
    created_at: str
    updated_at: str


class MediaListResponse(BaseModel):
    items: list[MediaItem]
    total: int
    page: int
    page_size: int


class MediaImportResponse(BaseModel):
    imported: int
    existing: int


class MediaPreprocessResponse(BaseModel):
    processed: int
    failed: int
