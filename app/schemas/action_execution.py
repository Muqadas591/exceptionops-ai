from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


ActionType = Literal[
    "email_draft",
    "accounting_simulation",
    "webhook_simulation",
]

ActionStatus = Literal[
    "pending",
    "in_progress",
    "succeeded",
    "failed",
    "uncertain",
]

ReconciliationOutcome = Literal[
    "confirmed_succeeded",
    "confirmed_not_executed",
]


class ActionRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    action_type: ActionType

    # Used only for the safe email-draft action.
    recipient: str | None = Field(
        default=None,
        max_length=320,
    )

    subject: str | None = Field(
        default=None,
        max_length=250,
    )

    message: str | None = Field(
        default=None,
        max_length=5000,
    )


class ActionExecutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    review_id: int
    action_type: str
    status: ActionStatus
    attempt_count: int
    idempotency_key: str
    request_fingerprint: str
    request_payload: dict[str, Any]
    result_payload: dict[str, Any] | None
    last_error: str | None
    executed_by: str
    created_at: datetime
    updated_at: datetime


class ActionReconciliationRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    outcome: ReconciliationOutcome

    # Require an operator explanation for the audit trail.
    note: str = Field(
        min_length=5,
        max_length=1000,
    )