from dataclasses import dataclass
from pathlib import Path

from task2_backend.common.enums import MediaType, TaskStatus


@dataclass(frozen=True)
class MediaAssetRecord:
    media_id: str
    asset_kind: str
    path: Path
    format: str
    sample_rate: int | None
    channels: int | None
    width: int | None
    height: int | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class MediaRecord:
    media_id: str
    source_path: Path
    media_type: MediaType
    detected_format: str | None
    duration_ms: int | None
    status: TaskStatus
    failure_reason: str | None
    created_at: str
    updated_at: str
    assets: tuple[MediaAssetRecord, ...] = ()
