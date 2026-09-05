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


class ApprovalPolicy(Base):
    """SQLAlchemy model for ApprovalPolicy configuration."""

    __tablename__ = "approval_policies"
    __table_args__ = (
        CheckConstraint(
            "discount_above_pct IS NOT NULL OR margin_below_pct IS NOT NULL OR payment_terms_above_days IS NOT NULL",
            name="ck_approval_policies_at_least_one_trigger",
        ),
        CheckConstraint(
            "payment_terms_above_days IS NULL OR payment_terms_above_days >= 0",
            name="ck_approval_policies_payment_terms_nonnegative",
        ),
        CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from",
            name="ck_approval_policies_effective_to_gt_from",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_tier_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("customer_tiers.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    discount_above_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    margin_below_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    payment_terms_above_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    approval_role: Mapped[str] = mapped_column(String(50), nullable=False)
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
