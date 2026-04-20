from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends

from task2_backend.api.dependencies import get_operations_service
from task2_backend.foundation.operations import OperationsService

router = APIRouter(prefix="/api/ops", tags=["ops"])


class MaintenanceRunResponse(BaseModel):
    run_id: int
    status: str
    started_at: str
    finished_at: str | None = None
    summary: dict[str, int | str] = Field(default_factory=dict)
    error_message: str | None = None


class OpsStatusResponse(BaseModel):
    media_status_counts: dict[str, int]
    task_status_counts: dict[str, int]
    pending_retry_jobs: int
    terminal_failure_jobs: int
    stale_lock_count: int
    last_maintenance_run: MaintenanceRunResponse | None = None


@router.get("/status", response_model=OpsStatusResponse)
def get_ops_status(
    service: OperationsService = Depends(get_operations_service),
) -> OpsStatusResponse:
    snapshot = service.get_status_snapshot()
    maintenance_run = None
    if snapshot.last_maintenance_run is not None:
        maintenance_run = MaintenanceRunResponse(
            run_id=snapshot.last_maintenance_run.id,
            status=snapshot.last_maintenance_run.status.value,
            started_at=snapshot.last_maintenance_run.started_at,
            finished_at=snapshot.last_maintenance_run.finished_at,
            summary=snapshot.last_maintenance_run.summary,
            error_message=snapshot.last_maintenance_run.error_message,
        )
    return OpsStatusResponse(
        media_status_counts=snapshot.media_status_counts,
        task_status_counts=snapshot.task_status_counts,
        pending_retry_jobs=snapshot.pending_retry_jobs,
        terminal_failure_jobs=snapshot.terminal_failure_jobs,
        stale_lock_count=snapshot.stale_lock_count,
        last_maintenance_run=maintenance_run,
    )
