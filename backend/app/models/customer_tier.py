from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.customer import Customer


class CustomerTier(Base):
    """CustomerTier model classifying customer commercial tiers (e.g. Standard, Silver, Gold, Platinum)."""

    __tablename__ = "customer_tiers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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

    # 1-to-Many Relationship: CustomerTier -> Customers
    customers: Mapped[List["Customer"]] = relationship(
        "Customer", back_populates="tier"
    )

    def __repr__(self) -> str:
        return f"<CustomerTier(id={self.id}, name='{self.name}', is_active={self.is_active})>"
