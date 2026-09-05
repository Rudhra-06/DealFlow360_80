from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.rbac import require_roles
from app.core.enums import RoleName
from app.db.session import get_db
from app.models.user import User
from app.schemas.portal import (
    PortalQuotationLineRead,
    PortalQuotationListItem,
    PortalQuotationRead,
    PortalQuoteVersionLineRead,
    PortalQuoteVersionRead,
)
from app.schemas.quote_negotiation import (
    QuoteNegotiationMessageCreate,
    QuoteNegotiationMessageRead,
    QuoteNegotiationRequestCreate,
    QuoteNegotiationRequestRead,
)
from app.schemas.quote_version import QuoteVersionCompareResult
from app.services.exceptions import (
    CommercialPolicyValidationError,
    InvalidReferenceError,
    QuoteAccessDeniedError,
    QuoteNotFoundError,
    ResourceNotFoundError,
)
from app.services.portal_quotation import PortalQuotationService
from app.services.quote_negotiation import QuoteNegotiationService

router = APIRouter()

CUSTOMER_ROLES = (RoleName.CUSTOMER,)


def _to_portal_quote_read(quote) -> PortalQuotationRead:
    lines = [
        PortalQuotationLineRead(
            id=l.id,
            product_id=l.product_id,
            product_sku=l.product.sku if getattr(l, "product", None) else "N/A",
            product_name=l.product.name if getattr(l, "product", None) else "N/A",
            quantity=l.quantity,
            unit_list_price=l.unit_list_price,
            line_discount_pct=l.line_discount_pct,
            effective_discount_pct=l.effective_discount_pct,
            gross_line_total=l.gross_line_total,
            discount_amount=l.discount_amount,
            net_line_total=l.net_line_total,
            billing_plan_name=l.billing_plan.name if getattr(l, "billing_plan", None) else None,
        )
        for l in quote.lines
    ]

    current_v_num = quote.current_version.version_number if getattr(quote, "current_version", None) else 1

    return PortalQuotationRead(
        id=quote.id,
        quote_number=quote.quote_number,
        status=quote.status,
        currency=quote.currency,
        payment_terms_days=quote.payment_terms_days,
        order_discount_pct=quote.order_discount_pct,
        gross_subtotal=quote.gross_subtotal,
        discount_amount=quote.discount_amount,
        net_total=quote.net_total,
        current_version_number=current_v_num,
        submitted_at=quote.submitted_at,
        created_at=quote.created_at,
        updated_at=quote.updated_at,
        lines=lines,
    )


def _to_portal_version_read(version) -> PortalQuoteVersionRead:
    lines = [
        PortalQuoteVersionLineRead(
            id=vl.id,
            quote_version_id=vl.quote_version_id,
            product_id=vl.product_id,
            product_sku_snapshot=vl.product_sku_snapshot,
            product_name_snapshot=vl.product_name_snapshot,
            quantity=vl.quantity,
            unit_list_price=vl.unit_list_price,
            line_discount_pct=vl.line_discount_pct,
            effective_discount_pct=vl.effective_discount_pct,
            gross_line_total=vl.gross_line_total,
            discount_amount=vl.discount_amount,
            net_line_total=vl.net_line_total,
        )
        for vl in version.lines
    ]

    return PortalQuoteVersionRead(
        id=version.id,
        quotation_id=version.quotation_id,
        version_number=version.version_number,
        source_type=version.source_type,
        status_snapshot=version.status_snapshot,
        approval_status=version.approval_status,
        currency=version.currency,
        payment_terms_days=version.payment_terms_days,
        order_discount_pct=version.order_discount_pct,
        gross_subtotal=version.gross_subtotal,
        discount_amount=version.discount_amount,
        net_total=version.net_total,
        created_at=version.created_at,
        lines=lines,
    )


@router.get(
    "/quotations",
    response_model=List[PortalQuotationListItem],
    summary="List safe quotations for customer portal user",
)
async def list_portal_quotations(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*CUSTOMER_ROLES)),
):
    service = PortalQuotationService(db)
    try:
        quotes = await service.list_portal_quotations(current_user.id, status=status_filter)
        res = []
        for q in quotes:
            current_v_num = q.current_version.version_number if getattr(q, "current_version", None) else 1
            res.append(
                PortalQuotationListItem(
                    id=q.id,
                    quote_number=q.quote_number,
                    status=q.status,
                    currency=q.currency,
                    net_total=q.net_total,
                    current_version_number=current_v_num,
                    created_at=q.created_at,
                    updated_at=q.updated_at,
                )
            )
        return res
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get(
    "/quotations/{quotation_id}",
    response_model=PortalQuotationRead,
    summary="Get safe details of quotation for customer portal",
)
async def get_portal_quotation(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*CUSTOMER_ROLES)),
):
    service = PortalQuotationService(db)
    try:
        quote = await service.get_portal_quotation(quotation_id, current_user.id)
        return _to_portal_quote_read(quote)
    except QuoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post(
    "/quotations/{quotation_id}/confirm",
    response_model=PortalQuotationRead,
    summary="Customer accepts and confirms quotation",
)
async def confirm_portal_quotation(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*CUSTOMER_ROLES)),
):
    service = PortalQuotationService(db)
    try:
        quote = await service.confirm_quotation(quotation_id, current_user.id)
        return _to_portal_quote_read(quote)
    except QuoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except CommercialPolicyValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/quotations/{quotation_id}/versions",
    response_model=List[PortalQuoteVersionRead],
    summary="List versions of quotation for customer portal",
)
async def list_portal_versions(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*CUSTOMER_ROLES)),
):
    service = PortalQuotationService(db)
    try:
        versions = await service.list_portal_versions(quotation_id, current_user.id)
        return [_to_portal_version_read(v) for v in versions]
    except QuoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get(
    "/quotations/{quotation_id}/versions/compare",
    response_model=QuoteVersionCompareResult,
    summary="Compare two versions of quotation for customer portal",
)
async def compare_portal_versions(
    quotation_id: int,
    from_version: int = Query(..., ge=1),
    to_version: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*CUSTOMER_ROLES)),
):
    service = PortalQuotationService(db)
    try:
        return await service.compare_portal_versions(
            quotation_id, from_version, to_version, current_user.id
        )
    except QuoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post(
    "/quotations/{quotation_id}/messages",
    response_model=QuoteNegotiationMessageRead,
    status_code=status.HTTP_201_CREATED,
    summary="Post customer comment or line question",
)
async def post_customer_message(
    quotation_id: int,
    obj_in: QuoteNegotiationMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*CUSTOMER_ROLES)),
):
    service = QuoteNegotiationService(db)
    try:
        msg = await service.add_customer_message(quotation_id, obj_in, current_user)
        return QuoteNegotiationMessageRead.model_validate(msg)
    except QuoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except CommercialPolicyValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/quotations/{quotation_id}/counter-offer",
    response_model=QuoteNegotiationRequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit customer counter-offer or terms revision request",
)
async def submit_customer_counter_offer(
    quotation_id: int,
    obj_in: QuoteNegotiationRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*CUSTOMER_ROLES)),
):
    service = QuoteNegotiationService(db)
    try:
        req = await service.submit_counter_offer(quotation_id, obj_in, current_user)
        return QuoteNegotiationRequestRead.model_validate(req)
    except QuoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except (CommercialPolicyValidationError, InvalidReferenceError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
