from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.billing_plan import BillingPlan
    from app.models.product import Product
    from app.models.quote_version import QuoteVersion


class QuoteVersionLine(Base):
    """SQLAlchemy model for snapshotting individual quotation lines inside a quote version."""

    __tablename__ = "quote_version_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quote_version_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quote_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_quote_line_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    billing_plan_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("billing_plans.id", ondelete="SET NULL"), nullable=True
    )

    product_sku_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    product_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)

    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_list_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    line_discount_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    effective_discount_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    gross_line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    net_line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    line_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    margin_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    margin_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    standard_discount_pct_snapshot: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    max_discount_pct_snapshot: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    quote_version: Mapped["QuoteVersion"] = relationship("QuoteVersion", back_populates="lines")
    product: Mapped[Optional["Product"]] = relationship("Product", lazy="selectin")
    billing_plan: Mapped[Optional["BillingPlan"]] = relationship("BillingPlan", lazy="selectin")
