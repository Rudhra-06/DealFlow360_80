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
    from app.models.billing_plan import BillingPlan
    from app.models.fulfillment_allocation import FulfillmentAllocation
    from app.models.product import Product
    from app.models.sales_order import SalesOrder


class SalesOrderLine(Base):
    """SQLAlchemy model for Sales Order Lines snapshotted from confirmed QuoteVersion lines."""

    __tablename__ = "sales_order_lines"
    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_sales_order_lines_quantity_gt_zero",
        ),
        CheckConstraint(
            "unit_list_price >= 0",
            name="ck_sales_order_lines_unit_list_price_ge_zero",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sales_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sales_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_quote_line_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("quotation_lines.id", ondelete="SET NULL"), nullable=True
    )
    source_quote_version_line_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("quote_version_lines.id", ondelete="SET NULL"), nullable=True
    )

    product_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    billing_plan_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("billing_plans.id", ondelete="SET NULL"), nullable=True
    )

    product_sku_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    product_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    product_description_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_list_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    line_discount_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="0.00")
    effective_discount_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="0.00")

    gross_line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    net_line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    line_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    margin_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    margin_pct: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)

    billing_type: Mapped[str] = mapped_column(String(20), nullable=False, default="ONE_TIME")  # ONE_TIME or RECURRING

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    sales_order: Mapped["SalesOrder"] = relationship("SalesOrder", back_populates="lines")
    product: Mapped[Optional["Product"]] = relationship("Product", lazy="selectin")
    billing_plan: Mapped[Optional["BillingPlan"]] = relationship("BillingPlan", lazy="selectin")
    fulfillment_allocations: Mapped[List["FulfillmentAllocation"]] = relationship(
        "FulfillmentAllocation", back_populates="sales_order_line", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def ordered_qty(self) -> Decimal:
        return self.quantity

    @property
    def shipped_qty(self) -> Decimal:
        if self.fulfillment_allocations:
            return sum((a.fulfilled_qty for a in self.fulfillment_allocations), Decimal("0.0000"))
        return Decimal("0.0000")

    def __repr__(self) -> str:
        return (
            f"<SalesOrderLine(id={self.id}, sales_order_id={self.sales_order_id}, "
            f"sku='{self.product_sku_snapshot}', qty={self.quantity}, net_total={self.net_line_total})>"
        )
