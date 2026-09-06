from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.rbac import require_roles
from app.core.roles import RoleName
from app.db.session import get_db
from app.models.user import User
from app.schemas.reports import ReportExportFormat, ReportExportRequest, ReportTypeEnum
from app.services.report_export import ReportExportService
from app.schemas.credit_note import CreditNoteApplyRequest, CreditNoteRead
from app.schemas.invoice import InvoiceRead
from app.schemas.subscription import (
    SubscriptionCancelRequest,
    SubscriptionQuantityChangeRequest,
    SubscriptionRead,
)
from app.services.billing import BillingService
from app.services.credit_note import CreditNoteService
from app.services.exceptions import (
    CreditApplicationError,
    CurrencyMismatchError,
    InvalidProrationDateError,
    ResourceNotFoundError,
    SubscriptionStateError,
)
from app.services.subscription import SubscriptionService

router = APIRouter()

READ_ROLES = (RoleName.ADMIN, RoleName.SALES_REP, RoleName.SALES_MANAGER, RoleName.FINANCE_OPERATIONS)
OPS_ROLES = (RoleName.ADMIN, RoleName.FINANCE_OPERATIONS)


@router.get(
    "/orders/{order_id}/billing",
    response_model=List[InvoiceRead],
    summary="List billing invoices for sales order",
)
async def get_order_billing(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
):
    service = BillingService(db)
    return await service.invoice_repo.list_by_order(db, order_id)


@router.post(
    "/orders/{order_id}/billing/initialize",
    response_model=List[InvoiceRead],
    summary="Initialize one-time & recurring billing for sales order",
)
async def initialize_order_billing(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*OPS_ROLES)),
):
    service = BillingService(db)
    try:
        return await service.initialize_order_billing(order_id, current_user.id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/invoices",
    response_model=List[InvoiceRead],
    summary="List customer invoices",
)
async def list_invoices(
    status_filter: Optional[str] = Query(None, alias="status"),
    customer_id: Optional[int] = Query(None),
    sales_order_id: Optional[int] = Query(None),
    invoice_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
):
    service = BillingService(db)
    return await service.invoice_repo.list_invoices(
        db,
        status=status_filter,
        customer_id=customer_id,
        sales_order_id=sales_order_id,
        invoice_type=invoice_type,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/invoices/{invoice_id}",
    response_model=InvoiceRead,
    summary="Get invoice details by ID",
)
async def get_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
):
    service = BillingService(db)
    inv = await service.invoice_repo.get_by_id(db, invoice_id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invoice {invoice_id} not found.")
    return inv


@router.get(
    "/invoices/{invoice_id}/pdf",
    summary="Export single invoice PDF document",
)
async def export_invoice_pdf(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = ReportExportService(db)
    req = ReportExportRequest(
        report_type=ReportTypeEnum.INVOICE,
        format=ReportExportFormat.PDF,
        invoice_id=invoice_id,
    )
    pdf_bytes, filename, mime_type = await service.export_report(req, current_user)
    return Response(
        content=pdf_bytes,
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    "/billing/generate-due",
    response_model=List[InvoiceRead],
    summary="Idempotently generate recurring invoices due as of date",
)
async def generate_due_invoices(
    as_of: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*OPS_ROLES)),
):
    service = BillingService(db)
    return await service.generate_due_recurring_invoices(as_of_date=as_of, actor_user_id=current_user.id)


@router.get(
    "/subscriptions",
    response_model=List[SubscriptionRead],
    summary="List active customer subscriptions",
)
async def list_subscriptions(
    status_filter: Optional[str] = Query(None, alias="status"),
    customer_id: Optional[int] = Query(None),
    sales_order_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
):
    service = SubscriptionService(db)
    return await service.sub_repo.list_subscriptions(
        db, status=status_filter, customer_id=customer_id, sales_order_id=sales_order_id, limit=limit, offset=offset
    )


@router.get(
    "/subscriptions/{subscription_id}",
    response_model=SubscriptionRead,
    summary="Get subscription details by ID",
)
async def get_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
):
    service = SubscriptionService(db)
    sub = await service.sub_repo.get_by_id(db, subscription_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Subscription {subscription_id} not found.")
    return sub


@router.post(
    "/subscriptions/{subscription_id}/change-quantity",
    response_model=SubscriptionRead,
    summary="Modify subscription quantity with mid-cycle proration calculation",
)
async def change_subscription_quantity(
    subscription_id: int,
    obj_in: SubscriptionQuantityChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*OPS_ROLES)),
):
    service = SubscriptionService(db)
    try:
        return await service.change_subscription_quantity(
            subscription_id=subscription_id,
            new_quantity=obj_in.new_quantity,
            effective_date=obj_in.effective_date,
            reason=obj_in.reason,
            actor_user_id=current_user.id,
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (SubscriptionStateError, InvalidProrationDateError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/subscriptions/{subscription_id}/cancel",
    response_model=SubscriptionRead,
    summary="Cancel subscription according to plan cancellation policy",
)
async def cancel_subscription(
    subscription_id: int,
    obj_in: SubscriptionCancelRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*OPS_ROLES)),
):
    service = SubscriptionService(db)
    try:
        return await service.cancel_subscription(
            subscription_id=subscription_id,
            effective_date=obj_in.effective_date,
            reason=obj_in.reason,
            actor_user_id=current_user.id,
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SubscriptionStateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/credit-notes",
    response_model=List[CreditNoteRead],
    summary="List credit notes",
)
async def list_credit_notes(
    status_filter: Optional[str] = Query(None, alias="status"),
    customer_id: Optional[int] = Query(None),
    sales_order_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
):
    service = CreditNoteService(db)
    return await service.list_credit_notes(
        status=status_filter, customer_id=customer_id, sales_order_id=sales_order_id, limit=limit, offset=offset
    )


@router.get(
    "/credit-notes/{credit_note_id}",
    response_model=CreditNoteRead,
    summary="Get credit note by ID",
)
async def get_credit_note(
    credit_note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
):
    service = CreditNoteService(db)
    try:
        return await service.get_credit_note(credit_note_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/credit-notes/{credit_note_id}/apply",
    response_model=CreditNoteRead,
    summary="Apply credit note amount to outstanding invoice balance",
)
async def apply_credit_note(
    credit_note_id: int,
    obj_in: CreditNoteApplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*OPS_ROLES)),
):
    service = CreditNoteService(db)
    try:
        return await service.apply_credit_note_to_invoice(
            credit_note_id=credit_note_id, invoice_id=obj_in.invoice_id, actor_user_id=current_user.id
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (CreditApplicationError, CurrencyMismatchError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
