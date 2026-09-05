from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.quotation import Quotation
    from app.models.quote_version_line import QuoteVersionLine
    from app.models.user import User


class QuoteVersion(Base):
    """SQLAlchemy model for immutable quotation version snapshots."""

    __tablename__ = "quote_versions"
    __table_args__ = (
        UniqueConstraint("quotation_id", "version_number", name="uq_quote_version_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status_snapshot: Mapped[str] = mapped_column(String(50), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    payment_terms_days: Mapped[int] = mapped_column(Integer, nullable=False)
    order_discount_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    gross_subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    net_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    margin_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    margin_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    weighted_effective_discount_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    blended_risk_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    source_negotiation_request_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    approval_status: Mapped[str] = mapped_column(String(50), nullable=False, default="APPROVED", server_default="APPROVED")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    quotation: Mapped["Quotation"] = relationship("Quotation", back_populates="versions")
    lines: Mapped[List["QuoteVersionLine"]] = relationship(
        "QuoteVersionLine", back_populates="quote_version", cascade="all, delete-orphan", lazy="selectin"
    )
    created_by_user: Mapped[Optional["User"]] = relationship("User", lazy="selectin")
