from __future__ import annotations

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class HumanReview(TimestampMixin, Base):
    __tablename__ = "human_reviews"

    __table_args__ = (
        UniqueConstraint(
            "workflow_run_id",
            name="uq_human_review_workflow_run",
        ),
        CheckConstraint(
            "status IN ("
            "'pending', 'correction_requested', "
            "'approved', 'rejected'"
            ")",
            name="ck_human_review_status",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    workflow_run_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    assigned_to: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )

    decision_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    decided_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    comments: Mapped[list["ReviewComment"]] = relationship(
    "ReviewComment",
    primaryjoin="HumanReview.id == ReviewComment.review_id",
    order_by="ReviewComment.id",
    cascade="all, delete-orphan",
)