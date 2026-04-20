from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from task2_backend.api.media import router as media_router
from task2_backend.api.reviews import router as review_router
from task2_backend.api.tasks import router as task_router
from task2_backend.common.exceptions import Task2Error
from task2_backend.foundation.config import load_config
from task2_backend.foundation.database import Database
from task2_backend.foundation.logging import setup_logging
from task2_backend.domains.annotation.repository import AnnotationRepository
from task2_backend.domains.annotation.services import AnnotationService
from task2_backend.domains.media.repository import MediaRepository
from task2_backend.domains.media.services import MediaService
from task2_backend.domains.review_export.repository import ReviewExportRepository
from task2_backend.domains.review_export.services import ReviewExportService


def create_app(config_path: str | None = None) -> FastAPI:
    app = FastAPI(title="Task2 Backend", version="0.1.0")

    backend_dir = Path(__file__).resolve().parents[2]
    config = load_config(config_path or str(backend_dir / "config.yaml"))
    setup_logging(config.paths.log_dir)

    database = Database(config.paths.database_path)
    database.init_schema()

    media_repository = MediaRepository(database)
    annotation_repository = AnnotationRepository(database)
    review_export_repository = ReviewExportRepository(database)

    app.state.config = config
    app.state.database = database
    app.state.media_service = MediaService(config, media_repository)
    app.state.annotation_service = AnnotationService(config, annotation_repository)
    app.state.review_export_service = ReviewExportService(config, review_export_repository)

    app.include_router(media_router)
    app.include_router(task_router)
    app.include_router(review_router)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.exception_handler(Task2Error)
    def task2_error_handler(_: Request, exc: Task2Error) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": exc.message,
                "entity_id": exc.entity_id,
                "retryable": exc.retryable,
            },
        )

    return app


app = create_app()
