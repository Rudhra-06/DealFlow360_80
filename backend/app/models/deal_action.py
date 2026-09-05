from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.deal_alert import DealAlert
    from app.models.quotation import Quotation
    from app.models.user import User


class DealAction(Base):
    """SQLAlchemy model for actionable nudges, follow-ups, and escalations triggered from deal alerts."""

    __tablename__ = "deal_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deal_alert_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deal_alerts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quotation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    action_type: Mapped[str] = mapped_column(String(50), nullable=False)  # NUDGE_SALES_REP, NUDGE_APPROVER, ESCALATE_MANAGER, ESCALATE_FINANCE, FOLLOW_UP_CUSTOMER
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="COMPLETED")

    target_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    message: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    alert: Mapped["DealAlert"] = relationship("DealAlert", back_populates="actions")
    quotation: Mapped["Quotation"] = relationship("Quotation", lazy="selectin")
    target_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[target_user_id], lazy="selectin")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id], lazy="selectin")

    def __repr__(self) -> str:
        return f"<DealAction(id={self.id}, alert_id={self.deal_alert_id}, type='{self.action_type}')>"
