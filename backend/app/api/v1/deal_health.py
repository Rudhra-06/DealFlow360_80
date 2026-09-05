from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import require_roles
from app.core.enums import RoleName
from app.db.session import get_db
from app.models.user import User
from app.schemas.deal_health import (
    DealHealthConfigCreate,
    DealHealthConfigRead,
    DealHealthConfigUpdate,
    DealHealthHistoryItem,
    DealHealthListItem,
    DealHealthScanRequest,
    DealHealthScanResult,
    DealHealthSnapshotRead,
)
from app.services.deal_health import DealHealthService
from app.services.exceptions import ResourceNotFoundError

router = APIRouter()

INTERNAL_ROLES = (
    RoleName.ADMIN,
    RoleName.SALES_MANAGER,
    RoleName.SALES_REP,
    RoleName.FINANCE_OPERATIONS,
)
ADMIN_MGR_ROLES = (RoleName.ADMIN, RoleName.SALES_MANAGER)


# --- CONFIGURATION ENDPOINTS ---

@router.get(
    "/deal-health-config",
    response_model=DealHealthConfigRead,
    summary="Get Active Deal Health Configuration",
)
async def get_active_deal_health_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*INTERNAL_ROLES)),
):
    service = DealHealthService(db)
    return await service.get_or_create_default_config()


@router.post(
    "/deal-health-config",
    response_model=DealHealthConfigRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Active Deal Health Configuration",
)
async def create_deal_health_config(
    obj_in: DealHealthConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMIN_MGR_ROLES)),
):
    service = DealHealthService(db)
    upd = DealHealthConfigUpdate(**obj_in.model_dump())
    return await service.update_config(upd, current_user.id)


@router.patch(
    "/deal-health-config/{id}",
    response_model=DealHealthConfigRead,
    summary="Update Active Deal Health Configuration",
)
async def update_deal_health_config(
    id: int,
    obj_in: DealHealthConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMIN_MGR_ROLES)),
):
    service = DealHealthService(db)
    return await service.update_config(obj_in, current_user.id)


# --- DEAL HEALTH MONITORING & DASHBOARD ENDPOINTS ---

@router.get(
    "/deal-health",
    response_model=List[DealHealthListItem],
    summary="Dashboard List of Deal Health Summaries",
)
async def list_deal_health_summaries(
    health_level: Optional[str] = Query(None, description="Filter by HEALTHY, WATCH, AT_RISK, CRITICAL"),
    sales_rep_id: Optional[int] = Query(None),
    customer_id: Optional[int] = Query(None),
    quotation_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search quote number or customer name"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*INTERNAL_ROLES)),
):
    service = DealHealthService(db)

    # Sales Rep role restricts visibility to own deals unless Admin/Manager
    rep_filter = sales_rep_id
    if current_user.role.name == RoleName.SALES_REP:
        rep_filter = current_user.id

    return await service.list_deal_health(
        health_level=health_level,
        sales_rep_id=rep_filter,
        customer_id=customer_id,
        quotation_status=quotation_status,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/deal-health/quotations/{quotation_id}",
    response_model=DealHealthSnapshotRead,
    summary="Get Current Deal Health for Quotation",
)
async def get_quotation_health(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*INTERNAL_ROLES)),
):
    service = DealHealthService(db)
    try:
        return await service.get_latest_health(quotation_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/deal-health/quotations/{quotation_id}/evaluate",
    response_model=DealHealthSnapshotRead,
    summary="Recalculate Deal Health for Quotation",
)
async def evaluate_quotation_health(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*INTERNAL_ROLES)),
):
    service = DealHealthService(db)
    try:
        return await service.evaluate_quotation_health(quotation_id, actor_user_id=current_user.id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/deal-health/quotations/{quotation_id}/history",
    response_model=List[DealHealthHistoryItem],
    summary="Get Deal Health Snapshot History for Quotation",
)
async def get_quotation_health_history(
    quotation_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*INTERNAL_ROLES)),
):
    service = DealHealthService(db)
    return await service.snapshot_repo.list_by_quotation(db, quotation_id, limit=limit)


@router.post(
    "/deal-health/run-scan",
    response_model=DealHealthScanResult,
    summary="Run Bulk Deal Health Scan",
)
async def run_bulk_deal_health_scan(
    payload: Optional[DealHealthScanRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMIN_MGR_ROLES)),
):
    service = DealHealthService(db)
    as_of = payload.as_of if payload else None
    return await service.run_bulk_scan(as_of=as_of)


deal_health_router = router

