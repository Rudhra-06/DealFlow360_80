from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.quotation_line import QuoteLine
    from app.models.quote_negotiation_request import QuoteNegotiationRequest


class QuoteNegotiationLineChange(Base):
    """SQLAlchemy model for requested line-level quantity/discount changes in a negotiation request."""

    __tablename__ = "quote_negotiation_line_changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    negotiation_request_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quote_negotiation_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quotation_line_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quotation_lines.id", ondelete="CASCADE"), nullable=False, index=True
    )

    requested_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 3), nullable=True)
    requested_line_discount_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    negotiation_request: Mapped["QuoteNegotiationRequest"] = relationship("QuoteNegotiationRequest", back_populates="line_changes")
    quotation_line: Mapped["QuoteLine"] = relationship("QuoteLine", lazy="selectin")
