
from __future__ import annotations

from typing import Any

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class BusinessEvaluation(TimestampMixin, Base):
    """
    Stores the latest deterministic business-rules evaluation
    for an ingested document.

    This table is separate from invoices because an extracted
    document is not yet a verified accounting invoice.
    """

    __tablename__ = "business_evaluations"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            name="uq_business_evaluation_document_id",
        ),
        CheckConstraint(
            "risk_score >= 0 AND risk_score <= 100",
            name="ck_business_evaluation_risk_score",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    decision: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        index=True,
    )

    risk_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    rules_version: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="phase4_v1",
    )

    findings: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
