from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    Boolean,
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
    from app.models.product import Product


class ProductRecommendationRule(Base):
    """SQLAlchemy model for co-purchase upsell/cross-sell recommendation configuration."""

    __tablename__ = "product_recommendation_rules"
    __table_args__ = (
        CheckConstraint(
            "source_product_id != suggested_product_id",
            name="ck_product_recommendation_rules_not_self",
        ),
        CheckConstraint(
            "recommended_qty > 0",
            name="ck_product_recommendation_rules_qty_gt_zero",
        ),
        CheckConstraint(
            "affinity_score >= 0",
            name="ck_product_recommendation_rules_affinity_ge_zero",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    suggested_product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )

    affinity_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default="1.00"
    )
    recommended_qty: Mapped[Decimal] = mapped_column(
        Numeric(14, 3), nullable=False, server_default="1.000"
    )

    is_promoted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    promotion_label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    min_margin_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
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
    source_product: Mapped["Product"] = relationship("Product", foreign_keys=[source_product_id], lazy="selectin")
    suggested_product: Mapped["Product"] = relationship("Product", foreign_keys=[suggested_product_id], lazy="selectin")
