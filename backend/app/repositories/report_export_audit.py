"""Report Export Audit Repository."""

from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report_export_audit import ReportExportAudit, ExportStatus


class ReportExportAuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, audit: ReportExportAudit) -> ReportExportAudit:
        self.session.add(audit)
        await self.session.flush()
        return audit

    async def get_by_user(
        self,
        user_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ReportExportAudit]:
        stmt = select(ReportExportAudit).order_by(desc(ReportExportAudit.generated_at))
        if user_id is not None:
            stmt = stmt.where(ReportExportAudit.user_id == user_id)
        stmt = stmt.limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
