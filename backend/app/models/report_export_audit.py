"""Report Export Audit Model.

Tracks all report export requests, formats, filters, execution status, and audit timestamps.
"""

import enum
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import String, Enum, DateTime, Integer, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ExportStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ReportExportAudit(Base):
    __tablename__ = "report_export_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    report_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    format: Mapped[str] = mapped_column(String(16), nullable=False)  # PDF or XLSX
    filters_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[ExportStatus] = mapped_column(
        Enum(ExportStatus, name="exportstatus"),
        default=ExportStatus.SUCCESS,
        nullable=False,
        index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin")
