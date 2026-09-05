from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any, List, Optional
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
    from app.models.billing_plan import BillingPlan
    from app.models.billing_schedule import BillingSchedule
    from app.models.customer import Customer
    from app.models.sales_order import SalesOrder
    from app.models.sales_order_line import SalesOrderLine


class Subscription(Base):
    """SQLAlchemy model for active recurring subscription streams created from sales orders."""

    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_subscriptions_quantity_gt_zero"),
        CheckConstraint("unit_price >= 0", name="ck_subscriptions_unit_price_ge_zero"),
        CheckConstraint("interval_months >= 1", name="ck_subscriptions_interval_months_ge_one"),
    )

    def __init__(self, **kwargs: Any) -> None:
        start_date = kwargs.get("start_date")
        if start_date:
            if "current_period_start" not in kwargs or kwargs["current_period_start"] is None:
                kwargs["current_period_start"] = start_date
            interval = kwargs.get("interval_months", 1)
            if "current_period_end" not in kwargs or kwargs["current_period_end"] is None:
                kwargs["current_period_end"] = start_date + timedelta(days=30 * interval)
            if "next_billing_date" not in kwargs or kwargs["next_billing_date"] is None:
                kwargs["next_billing_date"] = start_date + timedelta(days=30 * interval)
        if "quantity" not in kwargs or kwargs["quantity"] is None:
            kwargs["quantity"] = Decimal("1.0000")
        if "unit_price" not in kwargs or kwargs["unit_price"] is None:
            if "monthly_recurring_revenue" in kwargs and kwargs["monthly_recurring_revenue"] is not None:
                kwargs["unit_price"] = Decimal(str(kwargs["monthly_recurring_revenue"]))
            else:
                kwargs["unit_price"] = Decimal("0.00")
        super().__init__(**kwargs)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subscription_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    sales_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sales_orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sales_order_line_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sales_order_lines.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    billing_plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("billing_plans.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ACTIVE", index=True)  # ACTIVE, PENDING_CANCELLATION, CANCELLED, ENDED

    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    interval_months: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    proration_method: Mapped[str] = mapped_column(String(30), nullable=False, default="DAILY")
    cancellation_method: Mapped[str] = mapped_column(String(30), nullable=False, default="END_OF_PERIOD")

    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    next_billing_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    sales_order: Mapped["SalesOrder"] = relationship("SalesOrder", lazy="selectin")
    sales_order_line: Mapped["SalesOrderLine"] = relationship("SalesOrderLine", lazy="selectin")
    customer: Mapped["Customer"] = relationship("Customer", lazy="selectin")
    billing_plan: Mapped["BillingPlan"] = relationship("BillingPlan", lazy="selectin")
    schedules: Mapped[List["BillingSchedule"]] = relationship(
        "BillingSchedule", back_populates="subscription", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def monthly_recurring_revenue(self) -> Decimal:
        interval = self.interval_months if (self.interval_months and self.interval_months > 0) else 1
        total = Decimal(str(self.quantity or 0)) * Decimal(str(self.unit_price or 0))
        return (total / Decimal(str(interval))).quantize(Decimal("0.01"))

    @monthly_recurring_revenue.setter
    def monthly_recurring_revenue(self, value: Any) -> None:
        if value is not None:
            self.unit_price = Decimal(str(value))
            if not self.quantity:
                self.quantity = Decimal("1.0000")
            if not self.interval_months:
                self.interval_months = 1

    @property
    def billing_frequency(self) -> str:
        return "MONTHLY" if self.interval_months == 1 else f"{self.interval_months}_MONTHS"

    @billing_frequency.setter
    def billing_frequency(self, value: str) -> None:
        if value == "MONTHLY":
            self.interval_months = 1
        elif value == "QUARTERLY":
            self.interval_months = 3
        elif value in ("ANNUAL", "YEARLY"):
            self.interval_months = 12
        else:
            self.interval_months = 1

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, number='{self.subscription_number}', status='{self.status}')>"
