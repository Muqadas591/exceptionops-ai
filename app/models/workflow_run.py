from __future__ import annotations

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class WorkflowRun(TimestampMixin, Base):
    __tablename__ = "workflow_runs"

    __table_args__ = (
        CheckConstraint(
            "attempt_count >= 0",
            name="ck_workflow_run_attempt_count",
        ),
        Index("ix_workflow_runs_document_id", "document_id"),
        Index("ix_workflow_runs_status", "status"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="received",
    )

    idempotency_key: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        unique=True,
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    resolution_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    events: Mapped[list["WorkflowEvent"]] = relationship(
        "WorkflowEvent",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="WorkflowEvent.id",
    )