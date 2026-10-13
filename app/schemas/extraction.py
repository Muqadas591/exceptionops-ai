
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExtractedField(BaseModel):
    value: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str | None = None


class ExtractionResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    provider_name: str
    status: str
    fields: dict[str, dict[str, Any]]
    extracted_text_length: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime
