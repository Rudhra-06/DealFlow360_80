from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class DealHealthConfig(Base):
    """SQLAlchemy model for configurable deal health rules and weights."""

    __tablename__ = "deal_health_configs"
    __table_args__ = (
        CheckConstraint("healthy_min_score >= 0 AND healthy_min_score <= 100", name="ck_dhc_healthy_min"),
        CheckConstraint("watch_min_score >= 0 AND watch_min_score <= 100", name="ck_dhc_watch_min"),
        CheckConstraint("at_risk_min_score >= 0 AND at_risk_min_score <= 100", name="ck_dhc_at_risk_min"),
        CheckConstraint("stalled_quote_days >= 0", name="ck_dhc_stalled_quote_days"),
        CheckConstraint("approval_delay_hours >= 0", name="ck_dhc_approval_delay_hours"),
        CheckConstraint("negotiation_stall_days >= 0", name="ck_dhc_negotiation_stall_days"),
        CheckConstraint("discount_anomaly_threshold_pct >= 0", name="ck_dhc_discount_anomaly_threshold"),
        CheckConstraint("delivery_slippage_days >= 0", name="ck_dhc_delivery_slippage_days"),
        CheckConstraint("backorder_age_days >= 0", name="ck_dhc_backorder_age_days"),
        CheckConstraint("invoice_overdue_days >= 0", name="ck_dhc_invoice_overdue_days"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="Default Health Policy")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1", index=True)

    healthy_min_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="80.00")
    watch_min_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="60.00")
    at_risk_min_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="30.00")

    stalled_quote_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="5")
    approval_delay_hours: Mapped[int] = mapped_column(Integer, nullable=False, server_default="24")
    negotiation_stall_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="3")
    discount_anomaly_threshold_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="10.00")
    delivery_slippage_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="2")
    backorder_age_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="3")
    invoice_overdue_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

    weight_stalled_quote: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="20.00")
    weight_discount_anomaly: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="15.00")
    weight_approval_delay: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="10.00")
    weight_negotiation_stall: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="15.00")
    weight_delivery_slippage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="20.00")
    weight_backorder: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="10.00")
    weight_invoice_overdue: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="10.00")

    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    created_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_user_id], lazy="selectin")
    updated_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by_user_id], lazy="selectin")

    def __repr__(self) -> str:
        return f"<DealHealthConfig(id={self.id}, name='{self.name}', is_active={self.is_active})>"
