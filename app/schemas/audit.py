from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    event_type: str
    entity_type: str
    entity_id: str | None

    document_id: int | None
    workflow_run_id: int | None
    review_id: int | None
    action_id: int | None

    actor_type: str
    actor_id: str | None

    description: str
    event_metadata: dict[str, Any] | None

    created_at: datetime
    updated_at: datetime