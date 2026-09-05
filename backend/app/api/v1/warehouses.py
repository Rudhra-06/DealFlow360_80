from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.rbac import require_roles
from app.core.roles import RoleName
from app.db.session import get_db
from app.schemas.warehouse import WarehouseCreate, WarehouseRead, WarehouseUpdate
from app.services.exceptions import DuplicateResourceError, ResourceNotFoundError
from app.services.warehouse import WarehouseService

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
    response_model=List[WarehouseRead],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*READ_ROLES))],
)
async def list_warehouses(
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    service = WarehouseService(db)
    return await service.list_warehouses(is_active=is_active, limit=limit, offset=offset)


@router.get(
    "/{warehouse_id}",
    response_model=WarehouseRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*READ_ROLES))],
)
async def get_warehouse(
    warehouse_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = WarehouseService(db)
    try:
        return await service.get_warehouse_by_id(warehouse_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "",
    response_model=WarehouseRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*WRITE_ROLES))],
)
async def create_warehouse(
    payload: WarehouseCreate,
    db: AsyncSession = Depends(get_db),
):
    service = WarehouseService(db)
    try:
        return await service.create_warehouse(payload)
    except DuplicateResourceError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.patch(
    "/{warehouse_id}",
    response_model=WarehouseRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*WRITE_ROLES))],
)
async def update_warehouse(
    warehouse_id: int,
    payload: WarehouseUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = WarehouseService(db)
    try:
        return await service.update_warehouse(warehouse_id, payload)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DuplicateResourceError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
