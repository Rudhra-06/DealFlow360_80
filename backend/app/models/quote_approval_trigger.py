from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.approval_policy import ApprovalPolicy
    from app.models.quote_approval_step import QuoteApprovalStep


class QuoteApprovalTrigger(Base):
    """SQLAlchemy model for explaining approval step triggers."""

    __tablename__ = "quote_approval_triggers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    approval_step_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quote_approval_steps.id", ondelete="CASCADE"), nullable=False, index=True
    )
    approval_policy_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("approval_policies.id", ondelete="SET NULL"), nullable=True, index=True
    )

    trigger_code: Mapped[str] = mapped_column(String(100), nullable=False)
    actual_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    threshold_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    approval_step: Mapped["QuoteApprovalStep"] = relationship("QuoteApprovalStep", back_populates="triggers")
    approval_policy: Mapped[Optional["ApprovalPolicy"]] = relationship("ApprovalPolicy", lazy="selectin")
