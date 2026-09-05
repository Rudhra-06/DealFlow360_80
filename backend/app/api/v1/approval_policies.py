from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.rbac import require_roles
from app.core.roles import RoleName
from app.db.session import get_db
from app.models.user import User
from app.schemas.approval_policy import (
    ApprovalPolicyCreate,
    ApprovalPolicyRead,
    ApprovalPolicyUpdate,
)
from app.services.approval_policy import ApprovalPolicyService
from app.services.exceptions import (
    CommercialPolicyValidationError,
    InactiveReferenceError,
    InvalidReferenceError,
    ResourceNotFoundError,
)

router = APIRouter()

READ_ROLES = (
    RoleName.ADMIN,
    RoleName.SALES_REP,
    RoleName.SALES_MANAGER,
    RoleName.FINANCE_OPERATIONS,
)
WRITE_ROLES = (RoleName.ADMIN, RoleName.SALES_MANAGER, RoleName.FINANCE_OPERATIONS)


@router.get(
    "",
    response_model=List[ApprovalPolicyRead],
    status_code=status.HTTP_200_OK,
    summary="List Approval Policies",
)
async def list_approval_policies(
    customer_tier_id: Optional[int] = Query(None, description="Filter by CustomerTier ID"),
    approval_role: Optional[str] = Query(None, description="Filter by operational approver role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    effective_only: bool = Query(False, description="Filter to currently effective policies only"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
) -> List[ApprovalPolicyRead]:
    service = ApprovalPolicyService(db)
    return await service.list_policies(
        customer_tier_id=customer_tier_id,
        approval_role=approval_role,
        is_active=is_active,
        effective_only=effective_only,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{policy_id}",
    response_model=ApprovalPolicyRead,
    status_code=status.HTTP_200_OK,
    summary="Get Approval Policy by ID",
)
async def get_approval_policy(
    policy_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
) -> ApprovalPolicyRead:
    service = ApprovalPolicyService(db)
    try:
        return await service.get_policy_by_id(policy_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "",
    response_model=ApprovalPolicyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Approval Policy",
)
async def create_approval_policy(
    obj_in: ApprovalPolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> ApprovalPolicyRead:
    service = ApprovalPolicyService(db)
    try:
        return await service.create_policy(obj_in)
    except (CommercialPolicyValidationError, InvalidReferenceError, InactiveReferenceError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{policy_id}",
    response_model=ApprovalPolicyRead,
    status_code=status.HTTP_200_OK,
    summary="Update Approval Policy",
)
async def update_approval_policy(
    policy_id: int,
    obj_in: ApprovalPolicyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> ApprovalPolicyRead:
    service = ApprovalPolicyService(db)
    try:
        return await service.update_policy(policy_id, obj_in)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (CommercialPolicyValidationError, InvalidReferenceError, InactiveReferenceError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
