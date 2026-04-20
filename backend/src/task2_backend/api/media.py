from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

from task2_backend.api.dependencies import get_annotation_service, get_media_service
from task2_backend.domains.media.schemas import MediaImportResponse, MediaItem, MediaListResponse, MediaPreprocessResponse
from task2_backend.domains.annotation.services import AnnotationService
from task2_backend.domains.media.services import MediaService

router = APIRouter(prefix="/api/media", tags=["media"])


@router.get("", response_model=MediaListResponse)
def list_media(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    service: MediaService = Depends(get_media_service),
) -> MediaListResponse:
    return service.list_media(page, page_size, status)


@router.post("/import", response_model=MediaImportResponse)
def import_media(
    service: MediaService = Depends(get_media_service),
    annotation_service: AnnotationService = Depends(get_annotation_service),
) -> MediaImportResponse:
    response = service.import_media()
    annotation_service.sync_from_media()
    return response


@router.post("/preprocess", response_model=MediaPreprocessResponse)
def preprocess_media(
    service: MediaService = Depends(get_media_service),
    annotation_service: AnnotationService = Depends(get_annotation_service),
) -> MediaPreprocessResponse:
    response = service.preprocess_media()
    annotation_service.sync_from_media()
    return response


@router.get("/{media_id}", response_model=MediaItem)
def get_media(media_id: str, service: MediaService = Depends(get_media_service)) -> MediaItem:
    item = service.get_media(media_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Media not found: {media_id}")
    return item


@router.get("/{media_id}/stream")
def stream_media(media_id: str, service: MediaService = Depends(get_media_service)) -> FileResponse:
    path = service.get_stream_path(media_id)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail=f"Media not found: {media_id}")
    return FileResponse(path)


@router.get("/{media_id}/poster")
def get_media_poster(media_id: str, service: MediaService = Depends(get_media_service)) -> FileResponse:
    path = service.get_poster_path(media_id)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail=f"Poster not found: {media_id}")
    return FileResponse(path)


@router.get("/{media_id}/waveform")
def get_media_waveform(media_id: str, service: MediaService = Depends(get_media_service)) -> JSONResponse:
    payload = service.get_waveform_payload(media_id)
    if payload is None:
        raise HTTPException(status_code=404, detail=f"Waveform not found: {media_id}")
    return JSONResponse(payload)
