from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
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
    from app.models.invoice import Invoice
    from app.models.subscription import Subscription


class BillingSchedule(Base):
    """SQLAlchemy model for scheduled recurring billing occurrences."""

    __tablename__ = "billing_schedules"
    __table_args__ = (
        CheckConstraint("sequence >= 1", name="ck_billing_schedules_sequence_ge_one"),
        CheckConstraint("scheduled_amount >= 0", name="ck_billing_schedules_amount_ge_zero"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subscription_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invoice_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True
    )

    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    billing_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    scheduled_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="SCHEDULED", index=True)  # SCHEDULED, INVOICED, CANCELLED

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="schedules")
    invoice: Mapped[Optional["Invoice"]] = relationship("Invoice", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<BillingSchedule(id={self.id}, sub_id={self.subscription_id}, "
            f"seq={self.sequence}, status='{self.status}')>"
        )
