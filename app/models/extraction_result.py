
from sqlalchemy import (
    ForeignKey,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ExtractionResult(TimestampMixin, Base):
    __tablename__ = "extraction_results"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            name="uq_extraction_result_document_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provider_name: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="needs_review",
        nullable=False,
        index=True,
    )

    # Example:
    # {
    #   "invoice_number": {
    #       "value": "INV-001",
    #       "confidence": 0.90,
    #       "evidence": "Invoice Number: INV-001"
    #   }
    # }
    fields: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    extracted_text_length: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
