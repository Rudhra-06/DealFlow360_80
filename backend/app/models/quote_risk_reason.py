from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.quotation import Quotation
    from app.models.quotation_line import QuoteLine


class QuoteRiskReason(Base):
    """SQLAlchemy model for transactional normalized quotation risk reasons."""

    __tablename__ = "quote_risk_reasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quotation_line_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("quotation_lines.id", ondelete="CASCADE"), nullable=True, index=True
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    actual_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    threshold_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    quotation: Mapped["Quotation"] = relationship("Quotation", back_populates="risk_reasons")
    quotation_line: Mapped[Optional["QuoteLine"]] = relationship("QuoteLine", lazy="selectin")
