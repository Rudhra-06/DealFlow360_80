from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import require_roles
from app.core.enums import RoleName
from app.db.session import get_db
from app.models.user import User
from app.schemas.deal_health import (
    DealActionRead,
    DealAlertListItem,
    DealAlertRead,
    DealAlertResolveRequest,
    DealAlertDismissRequest,
    DealEscalateRequest,
    DealNudgeRequest,
)
from app.services.deal_action import DealActionService
from app.services.deal_alert import DealAlertService
from app.services.exceptions import CommercialPolicyValidationError, ResourceNotFoundError

router = APIRouter()

INTERNAL_ROLES = (
    RoleName.ADMIN,
    RoleName.SALES_MANAGER,
    RoleName.SALES_REP,
    RoleName.FINANCE_OPERATIONS,
)
ESCALATION_ROLES = (
    RoleName.ADMIN,
    RoleName.SALES_MANAGER,
    RoleName.FINANCE_OPERATIONS,
)


@router.get(
    "/deal-alerts",
    response_model=List[DealAlertListItem],
    summary="List Deal Alerts with Filters",
)
async def list_deal_alerts(
    status: Optional[str] = Query(None, description="OPEN, ACKNOWLEDGED, RESOLVED, DISMISSED"),
    severity: Optional[str] = Query(None, description="INFO, WARNING, HIGH, CRITICAL"),
    alert_type: Optional[str] = Query(None),
    quotation_id: Optional[int] = Query(None),
    assigned_user_id: Optional[int] = Query(None),
    sales_rep_id: Optional[int] = Query(None),
    customer_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*INTERNAL_ROLES)),
):
    service = DealAlertService(db)

    # Restrict Sales Rep to own alerts unless manager/admin
    rep_filter = sales_rep_id
    if current_user.role.name == RoleName.SALES_REP:
        rep_filter = current_user.id

    return await service.list_alerts(
        status=status,
        severity=severity,
        alert_type=alert_type,
        quotation_id=quotation_id,
        assigned_user_id=assigned_user_id,
        sales_rep_id=rep_filter,
        customer_id=customer_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/deal-alerts/{alert_id}",
    response_model=DealAlertRead,
    summary="Get Deal Alert Details",
)
async def get_deal_alert_detail(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*INTERNAL_ROLES)),
):
    service = DealAlertService(db)
    try:
        return await service.get_alert(alert_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/deal-alerts/{alert_id}/acknowledge",
    response_model=DealAlertRead,
    summary="Acknowledge Deal Alert",
)
async def acknowledge_deal_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*INTERNAL_ROLES)),
):
    service = DealAlertService(db)
    try:
        return await service.acknowledge_alert(alert_id, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CommercialPolicyValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/deal-alerts/{alert_id}/resolve",
    response_model=DealAlertRead,
    summary="Resolve Deal Alert",
)
async def resolve_deal_alert(
    alert_id: int,
    payload: DealAlertResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*INTERNAL_ROLES)),
):
    service = DealAlertService(db)
    try:
        return await service.resolve_alert(alert_id, payload.resolution_note, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/deal-alerts/{alert_id}/dismiss",
    response_model=DealAlertRead,
    summary="Dismiss Deal Alert",
)
async def dismiss_deal_alert(
    alert_id: int,
    payload: Optional[DealAlertDismissRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*INTERNAL_ROLES)),
):
    service = DealAlertService(db)
    reason = payload.reason if payload else None
    try:
        return await service.dismiss_alert(alert_id, reason, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/deal-alerts/{alert_id}/nudge",
    response_model=DealActionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger Actionable Nudge from Deal Alert",
)
async def trigger_nudge_from_alert(
    alert_id: int,
    payload: Optional[DealNudgeRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*INTERNAL_ROLES)),
):
    action_service = DealActionService(db)
    act_type = payload.action_type if payload else "NUDGE_SALES_REP"
    msg = payload.message if payload else None
    try:
        return await action_service.trigger_nudge(alert_id, act_type, msg, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/deal-alerts/{alert_id}/escalate",
    response_model=DealActionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Escalate Deal Alert to Management",
)
async def escalate_alert(
    alert_id: int,
    payload: Optional[DealEscalateRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ESCALATION_ROLES)),
):
    action_service = DealActionService(db)
    msg = payload.message if payload else None
    try:
        return await action_service.escalate(alert_id, msg, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
