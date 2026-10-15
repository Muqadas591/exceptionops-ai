from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


WorkflowStatus = Literal[
    "received",
    "extracted",
    "evaluated",
    "needs_review",
    "resolved",
    "failed",
    "cancelled",
]


class WorkflowEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_run_id: int
    event_type: str
    from_status: str | None
    to_status: str | None
    message: str
    event_metadata: dict[str, Any]
    created_at: datetime


class WorkflowResolveRequest(BaseModel):
    note: str = Field(
        min_length=3,
        max_length=2000,
        description="Explain the manual resolution.",
    )


class WorkflowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    status: WorkflowStatus
    idempotency_key: str | None
    attempt_count: int
    last_error: str | None
    resolution_note: str | None
    created_at: datetime
    updated_at: datetime
    events: list[WorkflowEventRead] = Field(default_factory=list)