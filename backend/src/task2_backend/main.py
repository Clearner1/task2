from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from task2_backend.api.media import router as media_router
from task2_backend.api.ops import router as ops_router
from task2_backend.api.reviews import router as review_router
from task2_backend.api.tasks import router as task_router
from task2_backend.common.exceptions import Task2Error
from task2_backend.foundation.config import load_config
from task2_backend.foundation.database import Database
from task2_backend.foundation.logging import setup_logging
from task2_backend.foundation.operations import MaintenanceRunner, OperationsService
from task2_backend.domains.annotation.repository import AnnotationRepository
from task2_backend.domains.annotation.services import AnnotationService
from task2_backend.domains.media.repository import MediaRepository
from task2_backend.domains.media.services import MediaService
from task2_backend.domains.review_export.repository import ReviewExportRepository
from task2_backend.domains.review_export.services import ReviewExportService


def create_app(config_path: str | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if app.state.config.runtime.worker_enabled:
            app.state.maintenance_runner.start()
        try:
            yield
        finally:
            app.state.maintenance_runner.stop()

    app = FastAPI(title="Task2 Backend", version="0.1.0", lifespan=lifespan)

    backend_dir = Path(__file__).resolve().parents[2]
    config = load_config(config_path or str(backend_dir / "config.yaml"))
    setup_logging(config.paths.log_dir)

    database = Database(config.paths.database_path)
    database.init_schema()

    media_repository = MediaRepository(database)
    annotation_repository = AnnotationRepository(database)
    review_export_repository = ReviewExportRepository(database)
    operations_service = OperationsService(database, config.retry)

    app.state.config = config
    app.state.database = database
    app.state.operations_service = operations_service
    app.state.media_service = MediaService(config, media_repository, operations_service)
    app.state.annotation_service = AnnotationService(config, annotation_repository)
    app.state.review_export_service = ReviewExportService(config, review_export_repository, operations_service)
    app.state.maintenance_runner = MaintenanceRunner(
        interval_seconds=config.runtime.maintenance_interval_seconds,
        shutdown_grace_seconds=config.runtime.shutdown_grace_seconds,
        replay_limit=config.runtime.max_concurrent_jobs,
        operations_service=operations_service,
        reclaim_expired_locks=app.state.annotation_service.reclaim_expired_locks,
        replay_handlers={
            "media_preprocess": lambda record: (
                app.state.media_service.replay_preprocess_failure(record.entity_id or ""),
                app.state.annotation_service.sync_from_media(),
            ),
            "export_reviewed_batch": lambda record: app.state.review_export_service.replay_export_failure(record.payload),
        },
    )

    app.include_router(media_router)
    app.include_router(task_router)
    app.include_router(review_router)
    app.include_router(ops_router)

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
