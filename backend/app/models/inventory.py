from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.warehouse import Warehouse


class Inventory(Base):
    """Inventory model mapping stock state per product across warehouses."""

    __tablename__ = "inventory"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "product_id", name="uq_inventory_warehouse_product"),
        CheckConstraint("on_hand_qty >= 0", name="ck_inventory_on_hand_qty_nonnegative"),
        CheckConstraint("reserved_qty >= 0", name="ck_inventory_reserved_qty_nonnegative"),
        CheckConstraint("reorder_level >= 0", name="ck_inventory_reorder_level_nonnegative"),
        CheckConstraint("reserved_qty <= on_hand_qty", name="ck_inventory_reserved_lte_on_hand"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    warehouse_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    on_hand_qty: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=Decimal("0.000"), nullable=False)
    reserved_qty: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=Decimal("0.000"), nullable=False)
    reorder_level: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=Decimal("0.000"), nullable=False)
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

    # Relationships
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="inventory_records")
    product: Mapped["Product"] = relationship("Product", back_populates="inventory_records")

    def __repr__(self) -> str:
        return (
            f"<Inventory(id={self.id}, warehouse_id={self.warehouse_id}, product_id={self.product_id}, "
            f"on_hand={self.on_hand_qty}, reserved={self.reserved_qty})>"
        )
