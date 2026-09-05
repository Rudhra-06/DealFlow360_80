from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.sales_order_line import SalesOrderLine


class InvoiceLine(Base):
    """SQLAlchemy model for items/charges within an invoice."""

    __tablename__ = "invoice_lines"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_invoice_lines_amount_ge_zero"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sales_order_line_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sales_order_lines.id", ondelete="SET NULL"), nullable=True
    )
    subscription_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True
    )

    line_type: Mapped[str] = mapped_column(String(30), nullable=False, default="ONE_TIME")  # ONE_TIME, RECURRING, PRORATION_CHARGE, ADJUSTMENT
    description: Mapped[str] = mapped_column(String(255), nullable=False)

    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, server_default="1.0000")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    billing_period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    billing_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    sales_order_line: Mapped[Optional["SalesOrderLine"]] = relationship("SalesOrderLine", lazy="selectin")

    def __repr__(self) -> str:
        return f"<InvoiceLine(id={self.id}, invoice_id={self.invoice_id}, amount={self.amount})>"
