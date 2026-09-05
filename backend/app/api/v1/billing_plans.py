from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.rbac import require_roles
from app.core.roles import RoleName
from app.db.session import get_db
from app.models.user import User
from app.schemas.billing_plan import (
    BillingPlanCreate,
    BillingPlanRead,
    BillingPlanUpdate,
)
from app.services.billing_plan import BillingPlanService
from app.services.exceptions import (
    CommercialPolicyValidationError,
    DuplicateResourceError,
    ResourceNotFoundError,
)

router = APIRouter()

READ_ROLES = (
    RoleName.ADMIN,
    RoleName.SALES_REP,
    RoleName.SALES_MANAGER,
    RoleName.FINANCE_OPERATIONS,
)
WRITE_ROLES = (RoleName.ADMIN, RoleName.FINANCE_OPERATIONS)


@router.get(
    "",
    response_model=List[BillingPlanRead],
    status_code=status.HTTP_200_OK,
    summary="List Billing Plans",
)
async def list_billing_plans(
    billing_type: Optional[str] = Query(None, description="Filter by billing type ('ONE_TIME' or 'RECURRING')"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
) -> List[BillingPlanRead]:
    service = BillingPlanService(db)
    return await service.list_plans(
        billing_type=billing_type,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{plan_id}",
    response_model=BillingPlanRead,
    status_code=status.HTTP_200_OK,
    summary="Get Billing Plan by ID",
)
async def get_billing_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
) -> BillingPlanRead:
    service = BillingPlanService(db)
    try:
        return await service.get_plan_by_id(plan_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "",
    response_model=BillingPlanRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Billing Plan",
)
async def create_billing_plan(
    obj_in: BillingPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> BillingPlanRead:
    service = BillingPlanService(db)
    try:
        return await service.create_plan(obj_in)
    except CommercialPolicyValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DuplicateResourceError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.patch(
    "/{plan_id}",
    response_model=BillingPlanRead,
    status_code=status.HTTP_200_OK,
    summary="Update Billing Plan",
)
async def update_billing_plan(
    plan_id: int,
    obj_in: BillingPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> BillingPlanRead:
    service = BillingPlanService(db)
    try:
        return await service.update_plan(plan_id, obj_in)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CommercialPolicyValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DuplicateResourceError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
