
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


Decision = Literal[
    "ready_for_matching",
    "needs_review",
    "blocked",
]


class BusinessFinding(BaseModel):
    rule_code: str = Field(min_length=1, max_length=80)
    severity: Literal["info", "low", "medium", "high", "critical"]
    message: str = Field(min_length=1, max_length=500)
    field: str | None = Field(default=None, max_length=80)


class BusinessEvaluationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    decision: Decision
    risk_score: int = Field(ge=0, le=100)
    rules_version: str
    findings: list[dict[str, Any]]
    summary: str
    created_at: datetime
    updated_at: datetime
