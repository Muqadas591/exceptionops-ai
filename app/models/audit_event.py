
from sqlalchemy import JSON, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class AuditEvent(TimestampMixin, Base):
    __tablename__ = "audit_events"

    __table_args__ = (
        Index(
            "ix_audit_events_document_created",
            "document_id",
            "created_at",
        ),
        Index(
            "ix_audit_events_workflow_created",
            "workflow_run_id",
            "created_at",
        ),
        Index(
            "ix_audit_events_review_created",
            "review_id",
            "created_at",
        ),
        Index(
            "ix_audit_events_action_created",
            "action_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    document_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )
    workflow_run_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )
    review_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )
    action_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )
    actor_type: Mapped[str] = mapped_column(
        String(30), default="system", nullable=False
    )
    actor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    event_metadata: Mapped[dict | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )
