from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.rbac import require_roles
from app.core.roles import RoleName
from app.db.session import get_db
from app.models.user import User
from app.schemas.fulfillment import (
    BackorderRead,
    FulfillmentPlanRead,
    FulfillmentPreviewRead,
    ManualOverrideRequest,
)
from app.services.exceptions import (
    InsufficientInventoryError,
    InvalidFulfillmentAllocationError,
    InvalidOrderStateError,
    ResourceNotFoundError,
)
from app.services.fulfillment import FulfillmentService

router = APIRouter()

READ_ROLES = (RoleName.ADMIN, RoleName.SALES_REP, RoleName.SALES_MANAGER, RoleName.FINANCE_OPERATIONS)
OPS_ROLES = (RoleName.ADMIN, RoleName.FINANCE_OPERATIONS)


@router.get(
    "/{order_id}/fulfillment/preview",
    response_model=FulfillmentPreviewRead,
    summary="Preview system fulfillment allocation recommendation",
)
async def preview_fulfillment(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
):
    service = FulfillmentService(db)
    try:
        return await service.preview_fulfillment(order_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{order_id}/fulfillment",
    response_model=FulfillmentPlanRead,
    summary="Get active fulfillment plan for sales order",
)
async def get_fulfillment_plan(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
):
    service = FulfillmentService(db)
    plan = await service.plan_repo.get_active_plan_by_order(db, order_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No active fulfillment plan for order {order_id}.")
    return plan


@router.post(
    "/{order_id}/fulfillment/accept",
    response_model=FulfillmentPlanRead,
    summary="Accept or initialize system fulfillment plan recommendation",
)
async def accept_fulfillment_plan(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*OPS_ROLES)),
):
    service = FulfillmentService(db)
    try:
        return await service.generate_and_reserve_initial_fulfillment(order_id, current_user.id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{order_id}/fulfillment/manual-override",
    response_model=FulfillmentPlanRead,
    summary="Manually override warehouse fulfillment allocation split",
)
async def manual_override_fulfillment(
    order_id: int,
    obj_in: ManualOverrideRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*OPS_ROLES)),
):
    service = FulfillmentService(db)
    try:
        alloc_dicts = [a.model_dump() for a in obj_in.allocations]
        return await service.apply_manual_override(order_id, alloc_dicts, current_user.id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (InvalidOrderStateError, InvalidFulfillmentAllocationError, InsufficientInventoryError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{order_id}/backorders",
    response_model=List[BackorderRead],
    summary="List backorders for sales order",
)
async def list_backorders(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
):
    service = FulfillmentService(db)
    return await service.backorder_repo.list_by_order(db, order_id)


@router.post(
    "/{order_id}/backorders/consolidate",
    response_model=List[BackorderRead],
    summary="Consolidate backorders with newly arrived warehouse inventory",
)
async def consolidate_backorders(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*OPS_ROLES)),
):
    service = FulfillmentService(db)
    try:
        return await service.consolidate_backorder(order_id, current_user.id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
