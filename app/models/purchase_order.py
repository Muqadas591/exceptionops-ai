
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class PurchaseOrder(TimestampMixin, Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    order_number: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    order_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(
        String(3), default="PKR", nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), default="open", nullable=False, index=True
    )

    supplier: Mapped["Supplier"] = relationship()
