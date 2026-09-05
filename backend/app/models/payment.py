from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
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
    from app.models.customer import Customer
    from app.models.payment_allocation import PaymentAllocation
    from app.models.user import User


class Payment(Base):
    """SQLAlchemy model for customer payment transactions."""

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payments_amount_gt_zero"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    payment_method: Mapped[str] = mapped_column(String(50), nullable=False, default="BANK_TRANSFER")
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    recorded_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="RECORDED", index=True)  # RECORDED, VOIDED

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", lazy="selectin")
    recorded_by_user: Mapped[Optional["User"]] = relationship("User", lazy="selectin")
    allocations: Mapped[List["PaymentAllocation"]] = relationship(
        "PaymentAllocation", back_populates="payment", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def invoice_id(self) -> Optional[int]:
        return self.__dict__.get("invoice_id")

    @invoice_id.setter
    def invoice_id(self, val: Optional[int]) -> None:
        self.__dict__["invoice_id"] = val

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, number='{self.payment_number}', amount={self.amount}, status='{self.status}')>"
