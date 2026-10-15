from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ReviewStatus = Literal[
    "pending",
    "correction_requested",
    "approved",
    "rejected",
]


class AssignReviewerRequest(BaseModel):
    reviewer: str = Field(min_length=3, max_length=255)


class ReviewCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class CorrectionRequest(BaseModel):
    instructions: str = Field(min_length=3, max_length=4000)


class ReviewDecisionRequest(BaseModel):
    note: str = Field(min_length=3, max_length=2000)


class ReviewCommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    review_id: int
    author: str
    comment_type: str
    body: str
    created_at: datetime


class HumanReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_run_id: int
    assigned_to: str | None
    status: ReviewStatus
    decision_note: str | None
    decided_by: str | None
    created_at: datetime
    updated_at: datetime
    comments: list[ReviewCommentRead] = Field(default_factory=list)