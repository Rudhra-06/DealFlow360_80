from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
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
    from app.models.customer import Customer
    from app.models.quote_audit_event import QuoteAuditEvent
    from app.models.quote_risk_reason import QuoteRiskReason
    from app.models.quotation_line import QuoteLine
    from app.models.user import User


class Quotation(Base):
    """SQLAlchemy model for Quotation commercial transactions."""

    __tablename__ = "quotations"
    __table_args__ = (
        CheckConstraint(
            "order_discount_pct >= 0 AND order_discount_pct <= 100",
            name="ck_quotations_order_discount_range",
        ),
        CheckConstraint(
            "payment_terms_days >= 0",
            name="ck_quotations_payment_terms_ge_zero",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quote_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sales_rep_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT", index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    payment_terms_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    order_discount_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default="0.00"
    )

    # Computed financial summary fields (populated by Pricing Engine & Margin Engine)
    gross_subtotal: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default="0.00"
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default="0.00"
    )
    net_total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default="0.00"
    )
    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default="0.00"
    )
    margin_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default="0.00"
    )
    margin_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default="0.00"
    )
    weighted_effective_discount_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default="0.00"
    )

    # Risk metrics
    blended_risk_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default="0.00"
    )
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="GREEN")

    # Timestamps
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Phase 4 Versioning & Confirmation Guarantees
    current_version_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latest_approved_version_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confirmed_quote_version_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    customer_confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    customer_confirmed_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", lazy="selectin")
    sales_rep: Mapped["User"] = relationship("User", foreign_keys=[sales_rep_id], lazy="selectin")
    customer_confirmed_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[customer_confirmed_by_user_id], lazy="selectin")
    lines: Mapped[List["QuoteLine"]] = relationship(
        "QuoteLine", back_populates="quotation", cascade="all, delete-orphan", lazy="selectin"
    )
    risk_reasons: Mapped[List["QuoteRiskReason"]] = relationship(
        "QuoteRiskReason", back_populates="quotation", cascade="all, delete-orphan", lazy="selectin"
    )
    audit_events: Mapped[List["QuoteAuditEvent"]] = relationship(
        "QuoteAuditEvent", back_populates="quotation", cascade="all, delete-orphan", lazy="selectin"
    )
    versions: Mapped[List["QuoteVersion"]] = relationship(
        "QuoteVersion", back_populates="quotation", cascade="all, delete-orphan", lazy="selectin"
    )
