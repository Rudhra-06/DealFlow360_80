from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.rbac import require_roles
from app.core.roles import RoleName
from app.db.session import get_db
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from app.services.customer import CustomerService
from app.services.exceptions import (
    DuplicateResourceError,
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
WRITE_ROLES = (
    RoleName.ADMIN,
    RoleName.SALES_REP,
    RoleName.SALES_MANAGER,
)


@router.get(
    "",
    response_model=List[CustomerRead],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*READ_ROLES))],
)
async def list_customers(
    tier_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    service = CustomerService(db)
    return await service.list_customers(
        tier_id=tier_id,
        is_active=is_active,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*READ_ROLES))],
)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = CustomerService(db)
    try:
        return await service.get_customer_by_id(customer_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*WRITE_ROLES))],
)
async def create_customer(
    payload: CustomerCreate,
    db: AsyncSession = Depends(get_db),
):
    service = CustomerService(db)
    try:
        return await service.create_customer(payload)
    except DuplicateResourceError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (InvalidReferenceError, InactiveReferenceError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{customer_id}",
    response_model=CustomerRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*WRITE_ROLES))],
)
async def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = CustomerService(db)
    try:
        return await service.update_customer(customer_id, payload)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DuplicateResourceError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (InvalidReferenceError, InactiveReferenceError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
