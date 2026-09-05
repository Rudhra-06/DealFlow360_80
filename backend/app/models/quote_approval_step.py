from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.quote_approval_trigger import QuoteApprovalTrigger
    from app.models.quotation import Quotation
    from app.models.user import User


class QuoteApprovalStep(Base):
    """SQLAlchemy model for quotation approval transaction step."""

    __tablename__ = "quote_approval_steps"
    __table_args__ = (
        UniqueConstraint("quotation_id", "approval_round", "sequence", name="uq_quote_approval_round_seq"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    approval_round: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    approval_role: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING", index=True)

    decided_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    decision_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    quotation: Mapped["Quotation"] = relationship("Quotation", lazy="selectin")
    decided_by_user: Mapped[Optional["User"]] = relationship("User", lazy="selectin")
    triggers: Mapped[List["QuoteApprovalTrigger"]] = relationship(
        "QuoteApprovalTrigger", back_populates="approval_step", cascade="all, delete-orphan", lazy="selectin"
    )
