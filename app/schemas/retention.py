
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class RetentionSummaryRead(BaseModel):
    total_documents: int
    available_document_content: int
    deletion_pending: int
    deleted_document_content: int

    audit_event_count: int
    oldest_audit_event_at: datetime | None

    document_content_retention_days: int
    audit_event_retention_days: int
    audit_events_older_than_review_threshold: int

    document_content_auto_delete_enabled: bool
    audit_event_auto_delete_enabled: bool


class DocumentRetentionCandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    file_size_bytes: int
    content_status: str
    created_at: datetime


class PurgeDocumentRequest(BaseModel):
    reason: str = Field(
        min_length=10,
        max_length=500,
        description="Explain why the document content is being purged.",
    )

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        cleaned = value.strip()

        if len(cleaned) < 10:
            raise ValueError(
                "The deletion reason must contain at least 10 "
                "non-whitespace characters."
            )

        return cleaned


class PurgeDocumentResponse(BaseModel):
    document_id: int
    content_status: str
    content_deleted_at: datetime | None
    message: str
