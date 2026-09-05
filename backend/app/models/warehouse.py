from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.inventory import Inventory


class Warehouse(Base):
    """Warehouse model representing fulfillment facilities in DealFlow360."""

    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fulfillment_priority: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    shipping_cost_weight: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("1.00"), nullable=False)
    base_shipping_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # 1-to-Many Relationship: Warehouse -> Inventory
    inventory_records: Mapped[List["Inventory"]] = relationship(
        "Inventory", back_populates="warehouse"
    )

    def __repr__(self) -> str:
        return f"<Warehouse(id={self.id}, code='{self.code}', name='{self.name}', is_active={self.is_active})>"
