from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.product_recommendation_rule import ProductRecommendationRule
    from app.models.quotation import Quotation
    from app.models.user import User


class QuoteRecommendationDismissal(Base):
    """SQLAlchemy model for persistent user dismissal of upsell recommendation rules per quote."""

    __tablename__ = "quote_recommendation_dismissals"
    __table_args__ = (
        UniqueConstraint("quotation_id", "recommendation_rule_id", name="uq_quote_rule_dismissal"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recommendation_rule_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("product_recommendation_rules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dismissed_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    quotation: Mapped["Quotation"] = relationship("Quotation", lazy="selectin")
    recommendation_rule: Mapped["ProductRecommendationRule"] = relationship("ProductRecommendationRule", lazy="selectin")
    dismissed_by_user: Mapped["User"] = relationship("User", lazy="selectin")
