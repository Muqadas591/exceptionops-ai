
from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ExceptionRecord(TimestampMixin, Base):
    __tablename__ = "exceptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("invoices.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    exception_type: Mapped[str] = mapped_column(
        String(80), nullable=False, index=True
    )
    severity: Mapped[str] = mapped_column(
        String(20), default="medium", nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), default="open", nullable=False, index=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
