from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.quotation import Quotation
    from app.models.quote_negotiation_line_change import QuoteNegotiationLineChange
    from app.models.quote_version import QuoteVersion
    from app.models.user import User


class QuoteNegotiationRequest(Base):
    """SQLAlchemy model for customer counter-offers and change requests."""

    __tablename__ = "quote_negotiation_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    base_quote_version_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quote_versions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    requested_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    request_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING", server_default="PENDING", index=True)

    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requested_order_discount_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    requested_payment_terms_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolution_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    quotation: Mapped["Quotation"] = relationship("Quotation")
    base_version: Mapped["QuoteVersion"] = relationship("QuoteVersion", lazy="selectin")
    requested_by_user: Mapped["User"] = relationship("User", foreign_keys=[requested_by_user_id], lazy="selectin")
    resolved_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[resolved_by_user_id], lazy="selectin")
    line_changes: Mapped[List["QuoteNegotiationLineChange"]] = relationship(
        "QuoteNegotiationLineChange", back_populates="negotiation_request", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def rejection_reason(self) -> Optional[str]:
        return self.resolution_reason
