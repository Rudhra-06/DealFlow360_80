from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.fulfillment_plan import FulfillmentPlan
    from app.models.sales_order_line import SalesOrderLine
    from app.models.warehouse import Warehouse


class FulfillmentAllocation(Base):
    """SQLAlchemy model for warehouse-line stock allocations within a fulfillment plan."""

    __tablename__ = "fulfillment_allocations"
    __table_args__ = (
        CheckConstraint("allocated_qty >= 0", name="ck_allocations_allocated_qty_ge_zero"),
        CheckConstraint("reserved_qty >= 0", name="ck_allocations_reserved_qty_ge_zero"),
        CheckConstraint("fulfilled_qty >= 0", name="ck_allocations_fulfilled_qty_ge_zero"),
        CheckConstraint("fulfilled_qty <= allocated_qty", name="ck_allocations_fulfilled_le_allocated"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fulfillment_plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fulfillment_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sales_order_line_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sales_order_lines.id", ondelete="CASCADE"), nullable=False, index=True
    )
    warehouse_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    allocated_qty: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    reserved_qty: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, server_default="0.0000")
    fulfilled_qty: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, server_default="0.0000")

    estimated_shipping_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0.00")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    fulfillment_plan: Mapped["FulfillmentPlan"] = relationship("FulfillmentPlan", back_populates="allocations")
    sales_order_line: Mapped["SalesOrderLine"] = relationship("SalesOrderLine", back_populates="fulfillment_allocations", lazy="selectin")
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<FulfillmentAllocation(id={self.id}, plan_id={self.fulfillment_plan_id}, "
            f"warehouse_id={self.warehouse_id}, allocated={self.allocated_qty})>"
        )
