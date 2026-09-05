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
    from app.models.quotation import Quotation
    from app.models.quote_version import QuoteVersion
    from app.models.sales_order_line import SalesOrderLine
    from app.models.user import User


class SalesOrder(Base):
    """SQLAlchemy model for Sales Orders converted from confirmed quotations."""

    __tablename__ = "sales_orders"
    __table_args__ = (
        CheckConstraint(
            "net_total >= 0",
            name="ck_sales_orders_net_total_ge_zero",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    quotation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("quotations.id", ondelete="RESTRICT"), unique=True, nullable=True, index=True
    )
    confirmed_quote_version_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("quote_versions.id", ondelete="RESTRICT"), nullable=True, index=True
    )

    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sales_rep_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True
    )

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="FULFILLMENT", index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    payment_terms_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)

    gross_subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0.00")
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0.00")
    net_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0.00")
    total_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0.00")
    margin_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0.00")
    margin_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="0.00")

    customer_confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    quotation: Mapped["Quotation"] = relationship("Quotation", lazy="selectin")
    confirmed_quote_version: Mapped["QuoteVersion"] = relationship("QuoteVersion", lazy="selectin")
    customer: Mapped["Customer"] = relationship("Customer", lazy="selectin")
    sales_rep: Mapped["User"] = relationship("User", lazy="selectin")
    lines: Mapped[List["SalesOrderLine"]] = relationship(
        "SalesOrderLine", back_populates="sales_order", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def confirmed_version_id(self) -> int:
        return self.confirmed_quote_version_id

    @property
    def total_amount(self) -> Decimal:
        return self.net_total

    @total_amount.setter
    def total_amount(self, value: Decimal) -> None:
        self.net_total = value



    def __repr__(self) -> str:
        return f"<SalesOrder(id={self.id}, order_number='{self.order_number}', status='{self.status}')>"
