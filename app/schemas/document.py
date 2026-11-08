
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    extension: str
    content_type: str
    file_size_bytes: int = Field(ge=1)
    checksum_sha256: str
    status: str

    content_status: str
    content_deleted_at: datetime | None
    content_deletion_reason: str | None
    content_deleted_by: str | None

    created_at: datetime
    updated_at: datetime
