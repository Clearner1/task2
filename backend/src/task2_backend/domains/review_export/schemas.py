from __future__ import annotations

from pydantic import BaseModel, Field

from task2_backend.common.enums import ReviewDecision


class ReviewRequest(BaseModel):
    reviewer_id: str
    decision: ReviewDecision
    notes: str = ""


class ReviewResponse(BaseModel):
    task_id: str
    decision: ReviewDecision
    reviewer_id: str
    reviewed_at: str


class ExportRequest(BaseModel):
    formats: list[str] = Field(default_factory=list)


class ExportResponse(BaseModel):
    batch_id: str
    status: str
    formats: list[str]
    output_paths: list[str]
    created_at: str
