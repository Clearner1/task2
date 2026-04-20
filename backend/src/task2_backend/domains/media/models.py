from dataclasses import dataclass
from pathlib import Path

from task2_backend.common.enums import MediaType, TaskStatus


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
