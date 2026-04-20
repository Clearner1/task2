from fastapi import APIRouter, Depends, HTTPException, Query

from task2_backend.api.dependencies import get_annotation_service
from task2_backend.common.exceptions import NotFoundError
from task2_backend.domains.annotation.schemas import AutosaveRequest, SubmitRequest, TaskDetail, TaskListResponse
from task2_backend.domains.annotation.services import AnnotationService

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=TaskListResponse)
def list_tasks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    assigned_to: str | None = None,
    service: AnnotationService = Depends(get_annotation_service),
) -> TaskListResponse:
    return service.list_tasks(page, page_size, status, assigned_to)


@router.get("/next", response_model=TaskDetail | None)
def next_task(
    annotator_id: str = Query(default="annotator_01"),
    service: AnnotationService = Depends(get_annotation_service),
) -> TaskDetail | None:
    return service.acquire_next_task(annotator_id)


@router.get("/{task_id}", response_model=TaskDetail)
def get_task(task_id: str, service: AnnotationService = Depends(get_annotation_service)) -> TaskDetail:
    try:
        return service.get_task_detail(task_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc


@router.post("/{task_id}/autosave", response_model=TaskDetail)
def autosave_task(
    task_id: str,
    payload: AutosaveRequest,
    service: AnnotationService = Depends(get_annotation_service),
) -> TaskDetail:
    try:
        return service.autosave(task_id, payload.annotator_id, payload.annotation)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc


@router.post("/{task_id}/submit", response_model=TaskDetail)
def submit_task(
    task_id: str,
    payload: SubmitRequest,
    service: AnnotationService = Depends(get_annotation_service),
) -> TaskDetail:
    try:
        return service.submit(task_id, payload.annotator_id, payload.annotation)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc
