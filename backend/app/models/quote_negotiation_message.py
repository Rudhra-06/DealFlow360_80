from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.quotation import Quotation
    from app.models.quotation_line import QuoteLine
    from app.models.user import User


class QuoteNegotiationMessage(Base):
    """SQLAlchemy model for line questions and negotiation messages."""

    __tablename__ = "quote_negotiation_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quote_version_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("quote_versions.id", ondelete="SET NULL"), nullable=True
    )
    quotation_line_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("quotation_lines.id", ondelete="SET NULL"), nullable=True
    )
    author_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    message_type: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_customer_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    quotation: Mapped["Quotation"] = relationship("Quotation")
    author_user: Mapped["User"] = relationship("User", lazy="selectin")
    line: Mapped[Optional["QuoteLine"]] = relationship("QuoteLine", lazy="selectin")
