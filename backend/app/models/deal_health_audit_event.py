from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.quotation import Quotation
    from app.models.sales_order import SalesOrder
    from app.models.user import User


class DealHealthAuditEvent(Base):
    """SQLAlchemy model for audit logging of deal health evaluations, alerts, and nudges."""

    __tablename__ = "deal_health_audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sales_order_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sales_orders.id", ondelete="SET NULL"), nullable=True
    )
    actor_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    quotation: Mapped["Quotation"] = relationship("Quotation", lazy="selectin")
    sales_order: Mapped[Optional["SalesOrder"]] = relationship("SalesOrder", lazy="selectin")
    actor_user: Mapped[Optional["User"]] = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<DealHealthAuditEvent(id={self.id}, type='{self.event_type}', quote_id={self.quotation_id})>"
