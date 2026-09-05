from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.rbac import require_roles
from app.core.enums import RoleName
from app.db.session import get_db
from app.models.user import User
from app.schemas.customer_portal_access import (
    CustomerPortalAccessCreate,
    CustomerPortalAccessRead,
    CustomerPortalAccessUpdate,
)
from app.services.customer_portal_access import CustomerPortalAccessService
from app.services.exceptions import (
    CommercialPolicyValidationError,
    InactiveReferenceError,
    InvalidReferenceError,
    ResourceNotFoundError,
)

router = APIRouter()

MANAGEMENT_ROLES = (RoleName.ADMIN, RoleName.SALES_REP, RoleName.SALES_MANAGER)


@router.post(
    "",
    response_model=CustomerPortalAccessRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create or re-activate customer portal user association",
)
async def create_customer_portal_access(
    obj_in: CustomerPortalAccessCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
):
    service = CustomerPortalAccessService(db)
    try:
        access = await service.create_access(obj_in)
        return CustomerPortalAccessRead.model_validate(access)
    except (InvalidReferenceError, InactiveReferenceError, CommercialPolicyValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/{access_id}",
    response_model=CustomerPortalAccessRead,
    summary="Update customer portal user association",
)
async def update_customer_portal_access(
    access_id: int,
    obj_in: CustomerPortalAccessUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
):
    service = CustomerPortalAccessService(db)
    try:
        access = await service.update_access(access_id, obj_in)
        return CustomerPortalAccessRead.model_validate(access)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "",
    response_model=List[CustomerPortalAccessRead],
    summary="List customer portal access mappings",
)
async def list_customer_portal_access(
    customer_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
):
    service = CustomerPortalAccessService(db)
    access_list = await service.list_access(
        customer_id=customer_id,
        user_id=user_id,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    return [CustomerPortalAccessRead.model_validate(a) for a in access_list]
