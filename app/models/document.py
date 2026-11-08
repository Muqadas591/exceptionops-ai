
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Document(TimestampMixin, Base):
    __tablename__ = "documents"

    __table_args__ = (
        UniqueConstraint(
            "checksum_sha256",
            name="uq_document_checksum_sha256",
        ),
        CheckConstraint(
            "content_status IN "
            "('available', 'deletion_pending', 'deleted')",
            name="ck_documents_content_status",
        ),
        Index(
            "ix_documents_content_status_created",
            "content_status",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    storage_key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    extension: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    content_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    checksum_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="received",
        nullable=False,
        index=True,
    )

    content_status: Mapped[str] = mapped_column(
        String(30),
        default="available",
        server_default="available",
        nullable=False,
        index=True,
    )

    content_deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    content_deletion_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    content_deleted_by: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
    )
