from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    CheckConstraint,
    Column,
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
    from app.models.billing_plan import BillingPlan
    from app.models.discount_policy import DiscountPolicy
    from app.models.product import Product
    from app.models.quotation import Quotation


class QuoteLine(Base):
    """SQLAlchemy model for Quotation individual product line item."""

    __tablename__ = "quotation_lines"
    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_quotation_lines_quantity_gt_zero",
        ),
        CheckConstraint(
            "line_discount_pct >= 0 AND line_discount_pct <= 100",
            name="ck_quotation_lines_discount_range",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    billing_plan_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("billing_plans.id", ondelete="RESTRICT"), nullable=True, index=True
    )

    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)

    # Historical Snapshots
    unit_list_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    line_discount_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default="0.00"
    )
    effective_discount_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default="0.00"
    )

    # Financial line totals
    gross_line_total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default="0.00"
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default="0.00"
    )
    net_line_total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default="0.00"
    )
    line_cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default="0.00"
    )
    margin_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default="0.00"
    )
    margin_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default="0.00"
    )

    # Resolved policy context & snapshots
    resolved_discount_policy_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("discount_policies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    recommendation_rule_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("product_recommendation_rules.id", ondelete="SET NULL"), nullable=True, index=True
    )
    standard_discount_pct_snapshot: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    max_discount_pct_snapshot: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )

    discount_overage_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default="0.00"
    )
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="GREEN")
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="MANUAL")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    quotation: Mapped["Quotation"] = relationship("Quotation", back_populates="lines")
    product: Mapped["Product"] = relationship("Product", lazy="selectin")
    billing_plan: Mapped[Optional["BillingPlan"]] = relationship("BillingPlan", lazy="selectin")
    resolved_discount_policy: Mapped[Optional["DiscountPolicy"]] = relationship(
        "DiscountPolicy", lazy="selectin"
    )
    recommendation_rule: Mapped[Optional["ProductRecommendationRule"]] = relationship(
        "ProductRecommendationRule", lazy="selectin"
    )
