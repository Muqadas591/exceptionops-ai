
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
    created_at: datetime
    updated_at: datetime
