from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
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
    from app.models.fulfillment_allocation import FulfillmentAllocation
    from app.models.sales_order import SalesOrder
    from app.models.user import User


class FulfillmentPlan(Base):
    """SQLAlchemy model for multi-warehouse fulfillment recommendation & override plans."""

    __tablename__ = "fulfillment_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sales_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sales_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    plan_type: Mapped[str] = mapped_column(String(50), nullable=False, default="SYSTEM_RECOMMENDED")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE")

    estimated_shipment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    estimated_shipping_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0.00")

    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    sales_order: Mapped["SalesOrder"] = relationship("SalesOrder", lazy="selectin")
    created_by_user: Mapped[Optional["User"]] = relationship("User", lazy="selectin")
    allocations: Mapped[List["FulfillmentAllocation"]] = relationship(
        "FulfillmentAllocation", back_populates="fulfillment_plan", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def is_manually_overridden(self) -> bool:
        return self.plan_type == "MANUAL_OVERRIDE"

    def __repr__(self) -> str:
        return (
            f"<FulfillmentPlan(id={self.id}, order_id={self.sales_order_id}, "
            f"type='{self.plan_type}', status='{self.status}')>"
        )

