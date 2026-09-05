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
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.invoice_line import InvoiceLine
    from app.models.sales_order import SalesOrder


class Invoice(Base):
    """SQLAlchemy model for customer invoices (one-time & recurring)."""

    __tablename__ = "invoices"
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="ck_invoices_total_amount_ge_zero"),
        CheckConstraint("credited_amount >= 0", name="ck_invoices_credited_amount_ge_zero"),
        CheckConstraint("paid_amount >= 0", name="ck_invoices_paid_amount_ge_zero"),
        CheckConstraint("balance_due >= 0", name="ck_invoices_balance_due_ge_zero"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    sales_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sales_orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    invoice_type: Mapped[str] = mapped_column(String(30), nullable=False, default="ONE_TIME")  # ONE_TIME, RECURRING, PRORATION, ADJUSTMENT
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ISSUED", index=True)  # DRAFT, ISSUED, PARTIALLY_PAID, PAID, CREDITED, CANCELLED
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0.00")
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0.00")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0.00")
    credited_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0.00")
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0.00")
    balance_due: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0.00")

    issue_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    billing_period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    billing_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    sales_order: Mapped["SalesOrder"] = relationship("SalesOrder", lazy="selectin")
    customer: Mapped["Customer"] = relationship("Customer", lazy="selectin")
    lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine", back_populates="invoice", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', total={self.total_amount}, status='{self.status}')>"
