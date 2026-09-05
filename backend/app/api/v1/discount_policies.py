from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.rbac import require_roles
from app.core.roles import RoleName
from app.db.session import get_db
from app.models.user import User
from app.schemas.discount_policy import (
    DiscountPolicyCreate,
    DiscountPolicyRead,
    DiscountPolicyResolutionRead,
    DiscountPolicyUpdate,
)
from app.services.discount_policy import DiscountPolicyService
from app.services.exceptions import (
    CommercialPolicyValidationError,
    InactiveReferenceError,
    InvalidReferenceError,
    PolicyAmbiguityError,
    ResourceNotFoundError,
)

router = APIRouter()

READ_ROLES = (
    RoleName.ADMIN,
    RoleName.SALES_REP,
    RoleName.SALES_MANAGER,
    RoleName.FINANCE_OPERATIONS,
)
WRITE_ROLES = (RoleName.ADMIN, RoleName.SALES_MANAGER)


@router.get(
    "",
    response_model=List[DiscountPolicyRead],
    status_code=status.HTTP_200_OK,
    summary="List Discount Policies",
)
async def list_discount_policies(
    customer_tier_id: Optional[int] = Query(None, description="Filter by target CustomerTier ID"),
    product_category_id: Optional[int] = Query(None, description="Filter by target ProductCategory ID"),
    product_id: Optional[int] = Query(None, description="Filter by target Product ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    effective_only: bool = Query(False, description="Filter to currently effective policies only"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
) -> List[DiscountPolicyRead]:
    service = DiscountPolicyService(db)
    return await service.list_policies(
        customer_tier_id=customer_tier_id,
        product_category_id=product_category_id,
        product_id=product_id,
        is_active=is_active,
        effective_only=effective_only,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/resolve",
    response_model=DiscountPolicyResolutionRead,
    status_code=status.HTTP_200_OK,
    summary="Resolve Applicable Discount Policy",
)
async def resolve_discount_policy(
    customer_tier_id: Optional[int] = Query(None, description="CustomerTier ID"),
    product_id: Optional[int] = Query(None, description="Product ID"),
    as_of: Optional[datetime] = Query(None, description="Optional target effective timestamp"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
) -> DiscountPolicyResolutionRead:
    service = DiscountPolicyService(db)
    policy, specificity = await service.get_applicable_policy(
        customer_tier_id=customer_tier_id,
        product_id=product_id,
        as_of=as_of,
    )
    return DiscountPolicyResolutionRead(applicable_policy=policy, specificity_level=specificity)


@router.get(
    "/{policy_id}",
    response_model=DiscountPolicyRead,
    status_code=status.HTTP_200_OK,
    summary="Get Discount Policy by ID",
)
async def get_discount_policy(
    policy_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
) -> DiscountPolicyRead:
    service = DiscountPolicyService(db)
    try:
        return await service.get_policy_by_id(policy_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "",
    response_model=DiscountPolicyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Discount Policy",
)
async def create_discount_policy(
    obj_in: DiscountPolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> DiscountPolicyRead:
    service = DiscountPolicyService(db)
    try:
        return await service.create_policy(obj_in)
    except (CommercialPolicyValidationError, InvalidReferenceError, InactiveReferenceError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PolicyAmbiguityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.patch(
    "/{policy_id}",
    response_model=DiscountPolicyRead,
    status_code=status.HTTP_200_OK,
    summary="Update Discount Policy",
)
async def update_discount_policy(
    policy_id: int,
    obj_in: DiscountPolicyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> DiscountPolicyRead:
    service = DiscountPolicyService(db)
    try:
        return await service.update_policy(policy_id, obj_in)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (CommercialPolicyValidationError, InvalidReferenceError, InactiveReferenceError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PolicyAmbiguityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
