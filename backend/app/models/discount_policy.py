from datetime import datetime
from typing import TYPE_CHECKING, Optional
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
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
    from app.models.customer_tier import CustomerTier
    from app.models.product import Product
    from app.models.product_category import ProductCategory


class DiscountPolicy(Base):
    """SQLAlchemy model for DiscountPolicy configuration."""

    __tablename__ = "discount_policies"
    __table_args__ = (
        CheckConstraint(
            "standard_discount_pct >= 0 AND standard_discount_pct <= 100",
            name="ck_discount_policies_standard_range",
        ),
        CheckConstraint(
            "max_discount_pct >= 0 AND max_discount_pct <= 100",
            name="ck_discount_policies_max_range",
        ),
        CheckConstraint(
            "standard_discount_pct <= max_discount_pct",
            name="ck_discount_policies_standard_lte_max",
        ),
        CheckConstraint(
            "product_id IS NULL OR product_category_id IS NULL",
            name="ck_discount_policies_not_both_product_and_category",
        ),
        CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from",
            name="ck_discount_policies_effective_to_gt_from",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_tier_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("customer_tiers.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    product_category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("product_categories.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    standard_discount_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default="0.00"
    )
    max_discount_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default="0.00"
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default="100")
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    effective_to: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    customer_tier: Mapped[Optional["CustomerTier"]] = relationship("CustomerTier", lazy="selectin")
    product_category: Mapped[Optional["ProductCategory"]] = relationship("ProductCategory", lazy="selectin")
    product: Mapped[Optional["Product"]] = relationship("Product", lazy="selectin")
