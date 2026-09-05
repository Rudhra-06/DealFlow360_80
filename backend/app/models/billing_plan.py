from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BillingPlan(Base):
    """SQLAlchemy model for BillingPlan configuration."""

    __tablename__ = "billing_plans"
    __table_args__ = (
        CheckConstraint(
            "payment_due_days >= 0",
            name="ck_billing_plans_payment_due_days_nonnegative",
        ),
        CheckConstraint(
            "(billing_type = 'ONE_TIME' AND billing_interval_months IS NULL) OR "
            "(billing_type = 'RECURRING' AND billing_interval_months IS NOT NULL AND billing_interval_months >= 1)",
            name="ck_billing_plans_type_and_interval",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    billing_type: Mapped[str] = mapped_column(String(20), nullable=False)  # ONE_TIME or RECURRING
    billing_interval_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    payment_due_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="30")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
