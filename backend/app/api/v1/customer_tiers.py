from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.rbac import require_roles
from app.core.roles import RoleName
from app.db.session import get_db
from app.schemas.customer_tier import CustomerTierCreate, CustomerTierRead, CustomerTierUpdate
from app.services.customer_tier import CustomerTierService
from app.services.exceptions import DuplicateResourceError, ResourceNotFoundError

router = APIRouter()

READ_ROLES = (
    RoleName.ADMIN,
    RoleName.SALES_REP,
    RoleName.SALES_MANAGER,
    RoleName.FINANCE_OPERATIONS,
)
WRITE_ROLES = (
    RoleName.ADMIN,
    RoleName.SALES_MANAGER,
)


@router.get(
    "",
    response_model=List[CustomerTierRead],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*READ_ROLES))],
)
async def list_customer_tiers(
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    service = CustomerTierService(db)
    return await service.list_tiers(is_active=is_active, limit=limit, offset=offset)


@router.get(
    "/{tier_id}",
    response_model=CustomerTierRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*READ_ROLES))],
)
async def get_customer_tier(
    tier_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = CustomerTierService(db)
    try:
        return await service.get_tier_by_id(tier_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "",
    response_model=CustomerTierRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*WRITE_ROLES))],
)
async def create_customer_tier(
    payload: CustomerTierCreate,
    db: AsyncSession = Depends(get_db),
):
    service = CustomerTierService(db)
    try:
        return await service.create_tier(payload)
    except DuplicateResourceError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.patch(
    "/{tier_id}",
    response_model=CustomerTierRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*WRITE_ROLES))],
)
async def update_customer_tier(
    tier_id: int,
    payload: CustomerTierUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = CustomerTierService(db)
    try:
        return await service.update_tier(tier_id, payload)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DuplicateResourceError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
