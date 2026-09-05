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
    from app.models.sales_order import SalesOrder
    from app.models.shipment_line import ShipmentLine
    from app.models.warehouse import Warehouse


class Shipment(Base):
    """SQLAlchemy model for physical shipments created from warehouse fulfillment allocations."""

    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shipment_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    sales_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sales_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    warehouse_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PLANNED", index=True)  # PLANNED, READY, SHIPPED, DELIVERED, CANCELLED

    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0.00")
    actual_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    sales_order: Mapped["SalesOrder"] = relationship("SalesOrder", lazy="selectin")
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", lazy="selectin")
    lines: Mapped[List["ShipmentLine"]] = relationship(
        "ShipmentLine", back_populates="shipment", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Shipment(id={self.id}, number='{self.shipment_number}', status='{self.status}')>"
