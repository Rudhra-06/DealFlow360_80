from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.deal_health_snapshot import DealHealthSnapshot


class DealHealthSignal(Base):
    """SQLAlchemy model for individual granular deal health risk signals contributing to a snapshot."""

    __tablename__ = "deal_health_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deal_health_snapshots.id", ondelete="CASCADE"), nullable=False, index=True
    )

    signal_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(30), nullable=False, default="WARNING")  # INFO, WARNING, HIGH, CRITICAL
    score_penalty: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="0.00")

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    metric_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)
    threshold_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)

    signal_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    snapshot: Mapped["DealHealthSnapshot"] = relationship("DealHealthSnapshot", back_populates="signals")

    def __repr__(self) -> str:
        return f"<DealHealthSignal(id={self.id}, type='{self.signal_type}', severity='{self.severity}', penalty={self.score_penalty})>"
