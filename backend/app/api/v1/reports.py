"""Reports API Router for Phase 6 Part 2."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Response, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.role import RoleName
from app.models.user import User
from app.api.dependencies.auth import get_current_active_user, require_roles
from app.schemas.reports import ReportExportRequest, ReportExportAuditListItem
from app.services.report_export import ReportExportService
from app.repositories.report_export_audit import ReportExportAuditRepository

router = APIRouter(prefix="/reports", tags=["Reports"])

INTERNAL_ROLES = [
    RoleName.ADMIN,
    RoleName.SALES_MANAGER,
    RoleName.SALES_REP,
    RoleName.FINANCE_OPERATIONS,
]


@router.post(
    "/export",
)
async def export_report(
    req: ReportExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = ReportExportService(db)
    file_bytes, filename, mime_type = await service.export_report(req, current_user)
    return Response(
        content=file_bytes,
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get(
    "/exports",
    response_model=List[ReportExportAuditListItem],
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_export_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    repo = ReportExportAuditRepository(db)
    role_names = [r.name for r in current_user.roles] if hasattr(current_user, "roles") else []
    user_filter = None if ("ADMIN" in role_names or "SALES_MANAGER" in role_names) else current_user.id
    return await repo.get_by_user(user_id=user_filter, limit=limit, offset=offset)
