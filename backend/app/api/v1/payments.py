from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.rbac import require_roles
from app.core.roles import RoleName
from app.db.session import get_db
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentRead
from app.services.exceptions import (
    CurrencyMismatchError,
    InvalidPaymentAllocationError,
    OverpaymentError,
    ResourceNotFoundError,
)
from app.services.payment import PaymentService

router = APIRouter()

READ_ROLES = (RoleName.ADMIN, RoleName.SALES_REP, RoleName.SALES_MANAGER, RoleName.FINANCE_OPERATIONS)
OPS_ROLES = (RoleName.ADMIN, RoleName.FINANCE_OPERATIONS)


@router.post(
    "/payments",
    response_model=PaymentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record customer payment and allocate across invoices",
)
async def record_payment(
    obj_in: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*OPS_ROLES)),
):
    service = PaymentService(db)
    try:
        allocations_data = [item.model_dump() for item in obj_in.allocations]
        return await service.record_payment(
            customer_id=obj_in.customer_id,
            amount=obj_in.amount,
            currency=obj_in.currency,
            payment_method=obj_in.payment_method,
            allocations_input=allocations_data,
            recorded_by_user_id=current_user.id,
            reference=obj_in.reference,
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (InvalidPaymentAllocationError, OverpaymentError, CurrencyMismatchError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/payments",
    response_model=List[PaymentRead],
    summary="List recorded payments",
)
async def list_payments(
    customer_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
):
    service = PaymentService(db)
    return await service.list_payments(
        customer_id=customer_id, status=status_filter, limit=limit, offset=offset
    )


@router.get(
    "/payments/{payment_id}",
    response_model=PaymentRead,
    summary="Get payment details by ID",
)
async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
):
    service = PaymentService(db)
    try:
        return await service.get_payment(payment_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
