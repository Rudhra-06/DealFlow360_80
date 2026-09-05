from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.credit_note_line import CreditNoteLine
    from app.models.customer import Customer
    from app.models.invoice import Invoice
    from app.models.sales_order import SalesOrder
    from app.models.subscription import Subscription


class CreditNote(Base):
    """SQLAlchemy model for credit notes issued from proration or cancellation credits."""

    __tablename__ = "credit_notes"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_credit_notes_amount_gt_zero"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    credit_note_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sales_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sales_orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    subscription_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True
    )
    invoice_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ISSUED", index=True)  # ISSUED, APPLIED, CANCELLED
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", lazy="selectin")
    sales_order: Mapped["SalesOrder"] = relationship("SalesOrder", lazy="selectin")
    subscription: Mapped[Optional["Subscription"]] = relationship("Subscription", lazy="selectin")
    invoice: Mapped[Optional["Invoice"]] = relationship("Invoice", lazy="selectin")
    lines: Mapped[List["CreditNoteLine"]] = relationship(
        "CreditNoteLine", back_populates="credit_note", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<CreditNote(id={self.id}, number='{self.credit_note_number}', amount={self.amount}, status='{self.status}')>"
