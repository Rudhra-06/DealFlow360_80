from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
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
    from app.models.credit_note import CreditNote


class CreditNoteLine(Base):
    """SQLAlchemy model for line items within a credit note."""

    __tablename__ = "credit_note_lines"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_credit_note_lines_amount_gt_zero"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    credit_note_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("credit_notes.id", ondelete="CASCADE"), nullable=False, index=True
    )

    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, server_default="1.0000")
    unit_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    credit_note: Mapped["CreditNote"] = relationship("CreditNote", back_populates="lines")

    def __repr__(self) -> str:
        return f"<CreditNoteLine(id={self.id}, credit_note_id={self.credit_note_id}, amount={self.amount})>"
