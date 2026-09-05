from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
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
    from app.models.fulfillment_allocation import FulfillmentAllocation
    from app.models.sales_order_line import SalesOrderLine
    from app.models.shipment import Shipment


class ShipmentLine(Base):
    """SQLAlchemy model for lines within a shipment."""

    __tablename__ = "shipment_lines"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_shipment_lines_quantity_gt_zero"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shipment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sales_order_line_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sales_order_lines.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    fulfillment_allocation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fulfillment_allocations.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    shipment: Mapped["Shipment"] = relationship("Shipment", back_populates="lines")
    sales_order_line: Mapped["SalesOrderLine"] = relationship("SalesOrderLine", lazy="selectin")
    fulfillment_allocation: Mapped["FulfillmentAllocation"] = relationship("FulfillmentAllocation", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ShipmentLine(id={self.id}, shipment_id={self.shipment_id}, qty={self.quantity})>"
