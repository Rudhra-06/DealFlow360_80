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
    from app.models.sales_order import SalesOrder
    from app.models.sales_order_line import SalesOrderLine


class Backorder(Base):
    """SQLAlchemy model tracking line-level unfulfilled backorders."""

    __tablename__ = "backorders"
    __table_args__ = (
        CheckConstraint("requested_qty > 0", name="ck_backorders_requested_qty_gt_zero"),
        CheckConstraint("backordered_qty >= 0", name="ck_backorders_backordered_qty_ge_zero"),
        CheckConstraint("fulfilled_from_backorder_qty >= 0", name="ck_backorders_fulfilled_from_backorder_ge_zero"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sales_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sales_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sales_order_line_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sales_order_lines.id", ondelete="CASCADE"), nullable=False, index=True
    )

    requested_qty: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    backordered_qty: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    fulfilled_from_backorder_qty: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False, server_default="0.0000"
    )

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="OPEN", index=True)  # OPEN, PARTIALLY_RESOLVED, RESOLVED, CANCELLED

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    sales_order: Mapped["SalesOrder"] = relationship("SalesOrder", lazy="selectin")
    sales_order_line: Mapped["SalesOrderLine"] = relationship("SalesOrderLine", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<Backorder(id={self.id}, order_id={self.sales_order_id}, "
            f"backordered_qty={self.backordered_qty}, status='{self.status}')>"
        )
