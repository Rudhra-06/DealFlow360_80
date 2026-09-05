from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.rbac import require_roles
from app.core.roles import RoleName
from app.db.session import get_db
from app.models.user import User
from app.schemas.order_audit_event import OrderAuditEventRead
from app.schemas.sales_order import SalesOrderListItem, SalesOrderRead
from app.repositories.order_audit_event import OrderAuditRepository
from app.services.exceptions import (
    ConfirmedVersionMissingError,
    OrderAlreadyExistsError,
    QuoteNotFoundError,
    ResourceNotFoundError,
)
from app.services.order import OrderService

router = APIRouter()

ORDER_READ_ROLES = (RoleName.ADMIN, RoleName.SALES_REP, RoleName.SALES_MANAGER, RoleName.FINANCE_OPERATIONS)
ORDER_WRITE_ROLES = (RoleName.ADMIN, RoleName.FINANCE_OPERATIONS)


@router.get(
    "",
    response_model=List[SalesOrderListItem],
    summary="List sales orders with role-based filtering",
)
async def list_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    customer_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ORDER_READ_ROLES)),
):
    service = OrderService(db)
    sales_rep_filter = None
    if current_user.role.name == RoleName.SALES_REP:
        sales_rep_filter = current_user.id

    return await service.list_orders(
        status=status_filter,
        customer_id=customer_id,
        sales_rep_id=sales_rep_filter,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{order_id}",
    response_model=SalesOrderRead,
    summary="Get detailed sales order by ID",
)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ORDER_READ_ROLES)),
):
    service = OrderService(db)
    try:
        order = await service.get_order_by_id(order_id)
        if current_user.role.name == RoleName.SALES_REP and order.sales_rep_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to order.")
        return order
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/by-quotation/{quotation_id}",
    response_model=SalesOrderRead,
    summary="Get sales order associated with quotation",
)
async def get_order_by_quotation(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ORDER_READ_ROLES)),
):
    service = OrderService(db)
    try:
        order = await service.get_order_by_quotation_id(quotation_id)
        if current_user.role.name == RoleName.SALES_REP and order.sales_rep_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to order.")
        return order
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{order_id}/audit",
    response_model=List[OrderAuditEventRead],
    summary="Get audit timeline for sales order",
)
async def get_order_audit(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ORDER_READ_ROLES)),
):
    service = OrderService(db)
    order = await service.get_order_by_id(order_id)
    if current_user.role.name == RoleName.SALES_REP and order.sales_rep_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to order audit.")

    audit_repo = OrderAuditRepository()
    return await audit_repo.list_events_by_order(db, order_id)
