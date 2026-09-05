from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.rbac import require_roles
from app.core.roles import RoleName
from app.db.session import get_db
from app.models.user import User
from app.schemas.shipment import ShipmentRead
from app.services.exceptions import (
    ResourceNotFoundError,
    ShipmentStateError,
)
from app.services.shipment import ShipmentService

router = APIRouter()

READ_ROLES = (RoleName.ADMIN, RoleName.SALES_REP, RoleName.SALES_MANAGER, RoleName.FINANCE_OPERATIONS)
OPS_ROLES = (RoleName.ADMIN, RoleName.FINANCE_OPERATIONS)


@router.get(
    "/{order_id}/shipments",
    response_model=List[ShipmentRead],
    summary="List shipments for sales order",
)
async def list_shipments(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
):
    service = ShipmentService(db)
    return await service.shipment_repo.list_by_order(db, order_id)


@router.post(
    "/{order_id}/shipments/generate",
    response_model=List[ShipmentRead],
    summary="Generate physical shipment records from fulfillment plan allocations",
)
async def generate_shipments(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*OPS_ROLES)),
):
    service = ShipmentService(db)
    try:
        return await service.generate_shipments_from_plan(order_id, current_user.id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{order_id}/shipments/{shipment_id}/ship",
    response_model=ShipmentRead,
    summary="Mark shipment shipped (decrements PostgreSQL inventory on_hand and reserved stock)",
)
async def ship_shipment(
    order_id: int,
    shipment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*OPS_ROLES)),
):
    service = ShipmentService(db)
    try:
        return await service.mark_shipment_shipped(shipment_id, current_user.id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ShipmentStateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{order_id}/shipments/{shipment_id}/deliver",
    response_model=ShipmentRead,
    summary="Mark shipment delivered to customer",
)
async def deliver_shipment(
    order_id: int,
    shipment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*OPS_ROLES)),
):
    service = ShipmentService(db)
    try:
        return await service.mark_shipment_delivered(shipment_id, current_user.id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ShipmentStateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
