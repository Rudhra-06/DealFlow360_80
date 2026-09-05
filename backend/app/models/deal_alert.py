from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
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
    from app.models.deal_action import DealAction
    from app.models.deal_health_snapshot import DealHealthSnapshot
    from app.models.quotation import Quotation
    from app.models.sales_order import SalesOrder
    from app.models.user import User


class DealAlert(Base):
    """SQLAlchemy model for deduplicated, actionable deal health alerts."""

    __tablename__ = "deal_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sales_order_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sales_orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    snapshot_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("deal_health_snapshots.id", ondelete="SET NULL"), nullable=True
    )

    alert_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(30), nullable=False, default="WARNING", index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="OPEN", index=True)  # OPEN, ACKNOWLEDGED, RESOLVED, DISMISSED

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    assigned_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    occurrence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    quotation: Mapped["Quotation"] = relationship("Quotation", lazy="selectin")
    sales_order: Mapped[Optional["SalesOrder"]] = relationship("SalesOrder", lazy="selectin")
    snapshot: Mapped[Optional["DealHealthSnapshot"]] = relationship("DealHealthSnapshot", lazy="selectin")
    assigned_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_user_id], lazy="selectin")
    acknowledged_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[acknowledged_by_user_id], lazy="selectin")
    resolved_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[resolved_by_user_id], lazy="selectin")
    actions: Mapped[List["DealAction"]] = relationship(
        "DealAction", back_populates="alert", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<DealAlert(id={self.id}, quote_id={self.quotation_id}, type='{self.alert_type}', status='{self.status}')>"
