
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Date,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Invoice(TimestampMixin, Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint(
            "supplier_id",
            "invoice_number",
            name="uq_invoice_supplier_number",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False)
    invoice_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(
        String(3), default="PKR", nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), default="received", nullable=False, index=True
    )

    supplier: Mapped["Supplier"] = relationship(back_populates="invoices")
