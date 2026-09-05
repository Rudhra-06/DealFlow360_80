from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.rbac import require_roles
from app.core.roles import RoleName
from app.db.session import get_db
from app.schemas.inventory import InventoryCreate, InventoryRead, InventoryUpdate
from app.services.exceptions import (
    DuplicateResourceError,
    InactiveReferenceError,
    InvalidReferenceError,
    InventoryValidationError,
    ResourceNotFoundError,
)
from app.services.inventory import InventoryService

router = APIRouter()

READ_ROLES = (
    RoleName.ADMIN,
    RoleName.SALES_REP,
    RoleName.SALES_MANAGER,
    RoleName.FINANCE_OPERATIONS,
)
WRITE_ROLES = (
    RoleName.ADMIN,
    RoleName.FINANCE_OPERATIONS,
)


@router.get(
    "",
    response_model=List[InventoryRead],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*READ_ROLES))],
)
async def list_inventory(
    warehouse_id: Optional[int] = Query(None),
    product_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    service = InventoryService(db)
    return await service.list_inventory(
        warehouse_id=warehouse_id,
        product_id=product_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{inventory_id}",
    response_model=InventoryRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*READ_ROLES))],
)
async def get_inventory(
    inventory_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = InventoryService(db)
    try:
        return await service.get_inventory_by_id(inventory_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "",
    response_model=InventoryRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*WRITE_ROLES))],
)
async def create_inventory(
    payload: InventoryCreate,
    db: AsyncSession = Depends(get_db),
):
    service = InventoryService(db)
    try:
        return await service.create_inventory(payload)
    except DuplicateResourceError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (InvalidReferenceError, InactiveReferenceError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{inventory_id}",
    response_model=InventoryRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*WRITE_ROLES))],
)
async def update_inventory(
    inventory_id: int,
    payload: InventoryUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = InventoryService(db)
    try:
        return await service.update_inventory(inventory_id, payload)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InventoryValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
