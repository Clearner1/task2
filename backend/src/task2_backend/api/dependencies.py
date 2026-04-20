from fastapi import Request

from task2_backend.domains.annotation.services import AnnotationService
from task2_backend.domains.media.services import MediaService
from task2_backend.domains.review_export.services import ReviewExportService
from task2_backend.foundation.operations import OperationsService


def get_media_service(request: Request) -> MediaService:
    return request.app.state.media_service


def get_annotation_service(request: Request) -> AnnotationService:
    return request.app.state.annotation_service


def get_review_export_service(request: Request) -> ReviewExportService:
    return request.app.state.review_export_service


def get_operations_service(request: Request) -> OperationsService:
    return request.app.state.operations_service
