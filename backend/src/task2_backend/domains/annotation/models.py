from dataclasses import dataclass

from task2_backend.common.enums import TaskStatus


@dataclass(frozen=True)
class TaskRecord:
    task_id: str
    media_id: str
    status: TaskStatus
    assigned_to: str | None
    lock_owner: str | None
    lock_acquired_at: str | None
    lock_expires_at: str | None
    submitted_at: str | None
    reviewed_at: str | None
    created_at: str
    updated_at: str
