from __future__ import annotations

from typing import Any

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ActionExecution(TimestampMixin, Base):
    __tablename__ = "action_executions"

    __table_args__ = (
        CheckConstraint(
            "status IN ("
            "'pending', "
            "'in_progress', "
            "'succeeded', "
            "'failed', "
            "'uncertain'"
            ")",
            name="ck_action_execution_status",
        ),
        CheckConstraint(
            "attempt_count >= 0",
            name="ck_action_execution_attempt_count",
        ),
        UniqueConstraint(
            "idempotency_key",
            name="uq_action_execution_idempotency_key",
        ),
        Index(
            "ix_action_execution_status_updated",
            "status",
            "updated_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    review_id: Mapped[int] = mapped_column(
        ForeignKey("human_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    action_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # A client must reuse the same key when repeating the same logical
    # request. A database uniqueness constraint prevents duplicate records.
    idempotency_key: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    # SHA-256 fingerprint of the action type and canonical request payload.
    # Prevents one idempotency key from being reused for different input.
    request_fingerprint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    request_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    result_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    executed_by: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )