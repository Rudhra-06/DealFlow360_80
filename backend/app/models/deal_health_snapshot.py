from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.deal_health_config import DealHealthConfig
    from app.models.deal_health_signal import DealHealthSignal
    from app.models.quotation import Quotation
    from app.models.sales_order import SalesOrder


class DealHealthSnapshot(Base):
    """SQLAlchemy model for point-in-time deal health evaluation snapshots."""

    __tablename__ = "deal_health_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sales_order_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sales_orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    config_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("deal_health_configs.id", ondelete="SET NULL"), nullable=True
    )

    health_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    health_level: Mapped[str] = mapped_column(String(30), nullable=False, index=True)  # HEALTHY, WATCH, AT_RISK, CRITICAL
    signal_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    summary: Mapped[str] = mapped_column(Text, nullable=False)

    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    quotation: Mapped["Quotation"] = relationship("Quotation", lazy="selectin")
    sales_order: Mapped[Optional["SalesOrder"]] = relationship("SalesOrder", lazy="selectin")
    config: Mapped[Optional["DealHealthConfig"]] = relationship("DealHealthConfig", lazy="selectin")
    signals: Mapped[List["DealHealthSignal"]] = relationship(
        "DealHealthSignal", back_populates="snapshot", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<DealHealthSnapshot(id={self.id}, quotation_id={self.quotation_id}, score={self.health_score}, level='{self.health_level}')>"
