from fastapi import APIRouter, Depends

from task2_backend.api.dependencies import get_review_export_service
from task2_backend.domains.review_export.schemas import ExportRequest, ExportResponse, ReviewRequest, ReviewResponse
from task2_backend.domains.review_export.services import ReviewExportService

router = APIRouter(tags=["review_export"])


@router.post("/api/reviews/{task_id}", response_model=ReviewResponse)
def review_task(
    task_id: str,
    payload: ReviewRequest,
    service: ReviewExportService = Depends(get_review_export_service),
) -> ReviewResponse:
    return service.review_task(task_id, payload)


@router.post("/api/exports", response_model=ExportResponse)
def export_reviews(
    payload: ExportRequest,
    service: ReviewExportService = Depends(get_review_export_service),
) -> ExportResponse:
    return service.export_reviews(payload)


@router.get("/api/exports/{batch_id}", response_model=ExportResponse)
def get_export_batch(
    batch_id: str,
    service: ReviewExportService = Depends(get_review_export_service),
) -> ExportResponse:
    return service.get_export_batch(batch_id)
