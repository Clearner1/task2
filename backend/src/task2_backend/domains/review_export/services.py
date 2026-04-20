from __future__ import annotations

import json
from pathlib import Path

from task2_backend.common.enums import ReviewDecision
from task2_backend.common.exceptions import ExportWriteError, NotFoundError
from task2_backend.common.time import isoformat, now_utc
from task2_backend.domains.review_export.repository import ReviewExportRepository
from task2_backend.domains.review_export.schemas import ExportRequest, ExportResponse, ReviewRequest, ReviewResponse
from task2_backend.foundation.config import AppConfig
from task2_backend.foundation.retry import run_with_retry


class ReviewExportService:
    def __init__(self, config: AppConfig, repository: ReviewExportRepository):
        self.config = config
        self.repository = repository

    def review_task(self, task_id: str, payload: ReviewRequest) -> ReviewResponse:
        reviewed_at = isoformat(now_utc())
        self.repository.save_review(task_id, payload.reviewer_id, payload.decision.value, payload.notes, reviewed_at)
        return ReviewResponse(
            task_id=task_id,
            decision=payload.decision,
            reviewer_id=payload.reviewer_id,
            reviewed_at=reviewed_at,
        )

    def export_reviews(self, request: ExportRequest) -> ExportResponse:
        formats = request.formats or list(self.config.export.formats)
        created_at = isoformat(now_utc())
        rows = self.repository.get_export_rows()
        records = [self._serialize_row(row) for row in rows]

        output_paths: list[str] = []
        for fmt in formats:
            output_path = self.config.paths.export_dir / f"export_{created_at.replace(':', '-')}.{fmt}"
            run_with_retry(
                "write_export",
                output_path.name,
                self.config.retry,
                lambda output_path=output_path, fmt=fmt, records=records: self._write_export(output_path, fmt, records),
            )
            output_paths.append(str(output_path))

        batch = self.repository.create_export_batch(formats, output_paths, created_at)
        return ExportResponse(
            batch_id=batch.batch_id,
            status=batch.status,
            formats=formats,
            output_paths=output_paths,
            created_at=created_at,
        )

    def get_export_batch(self, batch_id: str) -> ExportResponse:
        batch = self.repository.get_export_batch(batch_id)
        if batch is None:
            raise NotFoundError(f"Export batch not found: {batch_id}", entity_id=batch_id)
        return ExportResponse(
            batch_id=batch.batch_id,
            status=batch.status,
            formats=[item for item in batch.formats.split(",") if item],
            output_paths=[item for item in batch.output_paths.split("\n") if item],
            created_at=batch.created_at,
        )

    @staticmethod
    def _write_export(path: Path, fmt: str, records: list[dict[str, object]]) -> None:
        try:
            if fmt == "json":
                path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
                return
            if fmt == "jsonl":
                path.write_text(
                    "\n".join(json.dumps(record, ensure_ascii=False) for record in records),
                    encoding="utf-8",
                )
                return
            raise ExportWriteError(f"Unsupported export format: {fmt}", entity_id=fmt)
        except OSError as exc:
            raise ExportWriteError(f"Failed to write export: {path}") from exc

    @staticmethod
    def _serialize_row(row) -> dict[str, object]:
        return {
            "media_id": row["media_id"],
            "source_path": row["source_path"],
            "media_type": row["media_type"],
            "detected_format": row["detected_format"],
            "duration_ms": row["duration_ms"],
            "annotation": {
                "primary_emotion": row["primary_emotion"],
                "secondary_emotions": json.loads(row["secondary_emotions"]),
                "intensity": row["intensity"],
                "confidence": row["confidence"],
                "valence": row["valence"],
                "arousal": row["arousal"],
                "notes": row["notes"],
            },
            "annotator": {
                "annotator_id": row["annotator_id"],
                "submitted_at": row["submitted_at"],
            },
            "review": {
                "status": ReviewDecision(row["decision"]).value,
                "reviewer_id": row["reviewer_id"],
                "reviewed_at": row["reviewed_at"],
            },
        }
