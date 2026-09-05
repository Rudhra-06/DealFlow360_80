from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.rbac import require_roles
from app.core.enums import RoleName
from app.db.session import get_db
from app.models.user import User
from app.schemas.quote_audit_event import QuoteAuditEventRead
from app.schemas.quotation import (
    QuotationCreate,
    QuotationListItem,
    QuotationRead,
    QuotationUpdate,
    QuoteRecalculationRead,
)
from app.schemas.quotation_line import QuoteLineCreate, QuoteLineUpdate
from app.services.exceptions import (
    CurrencyMismatchError,
    InactiveReferenceError,
    InvalidReferenceError,
    QuoteAccessDeniedError,
    QuoteLineNotFoundError,
    QuoteNotEditableError,
    QuoteNotFoundError,
    QuotationValidationError,
)
from app.services.quotation import QuotationService

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
)


@router.get(
    "",
    response_model=List[QuotationListItem],
    status_code=status.HTTP_200_OK,
    summary="List Quotations",
)
async def list_quotations(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by quotation status"),
    customer_id: Optional[int] = Query(None, description="Filter by Customer ID"),
    sales_rep_id: Optional[int] = Query(None, description="Filter by Sales Rep user ID"),
    search: Optional[str] = Query(None, description="Search by quote number or customer name/code"),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
) -> List[QuotationListItem]:
    service = QuotationService(db)
    return await service.list_quotations(
        status=status_filter,
        customer_id=customer_id,
        sales_rep_id=sales_rep_id,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=QuotationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Quotation",
)
async def create_quotation(
    obj_in: QuotationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> QuotationRead:
    service = QuotationService(db)
    try:
        return await service.create_quotation(obj_in, current_user)
    except (InvalidReferenceError, InactiveReferenceError, QuotationValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{quotation_id}",
    response_model=QuotationRead,
    status_code=status.HTTP_200_OK,
    summary="Get Quotation Details",
)
async def get_quotation(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
) -> QuotationRead:
    service = QuotationService(db)
    try:
        return await service.get_quotation_by_id(quotation_id)
    except QuoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{quotation_id}",
    response_model=QuotationRead,
    status_code=status.HTTP_200_OK,
    summary="Update Quotation Header",
)
async def update_quotation(
    quotation_id: int,
    obj_in: QuotationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> QuotationRead:
    service = QuotationService(db)
    try:
        return await service.update_quotation(quotation_id, obj_in, current_user)
    except QuoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuoteNotEditableError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except (InvalidReferenceError, InactiveReferenceError, QuotationValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{quotation_id}/lines",
    response_model=QuotationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add Product Line to Quotation",
)
async def add_quote_line(
    quotation_id: int,
    obj_in: QuoteLineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> QuotationRead:
    service = QuotationService(db)
    try:
        return await service.add_quote_line(quotation_id, obj_in, current_user)
    except QuoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuoteNotEditableError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except (CurrencyMismatchError, InvalidReferenceError, InactiveReferenceError, QuotationValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{quotation_id}/lines/{line_id}",
    response_model=QuotationRead,
    status_code=status.HTTP_200_OK,
    summary="Update Quotation Line",
)
async def update_quote_line(
    quotation_id: int,
    line_id: int,
    obj_in: QuoteLineUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> QuotationRead:
    service = QuotationService(db)
    try:
        return await service.update_quote_line(quotation_id, line_id, obj_in, current_user)
    except (QuoteNotFoundError, QuoteLineNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuoteNotEditableError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except (InvalidReferenceError, InactiveReferenceError, QuotationValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{quotation_id}/lines/{line_id}",
    response_model=QuotationRead,
    status_code=status.HTTP_200_OK,
    summary="Remove Quotation Line",
)
async def remove_quote_line(
    quotation_id: int,
    line_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> QuotationRead:
    service = QuotationService(db)
    try:
        return await service.remove_quote_line(quotation_id, line_id, current_user)
    except (QuoteNotFoundError, QuoteLineNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuoteNotEditableError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post(
    "/{quotation_id}/recalculate",
    response_model=QuoteRecalculationRead,
    status_code=status.HTTP_200_OK,
    summary="Recalculate Quotation",
)
async def recalculate_quotation(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> QuoteRecalculationRead:
    service = QuotationService(db)
    try:
        quote = await service.recalculate_quotation(quotation_id, current_user)
        return QuoteRecalculationRead(quotation=quote)
    except QuoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuoteNotEditableError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post(
    "/{quotation_id}/cancel",
    response_model=QuotationRead,
    status_code=status.HTTP_200_OK,
    summary="Cancel Quotation",
)
async def cancel_quotation(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> QuotationRead:
    service = QuotationService(db)
    try:
        return await service.cancel_quotation(quotation_id, current_user)
    except QuoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuoteNotEditableError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get(
    "/{quotation_id}/audit",
    response_model=List[QuoteAuditEventRead],
    status_code=status.HTTP_200_OK,
    summary="Get Quotation Audit Trail",
)
async def get_quotation_audit(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
) -> List[QuoteAuditEventRead]:
    service = QuotationService(db)
    try:
        return await service.get_audit_events(quotation_id)
    except QuoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ----------------------------------------------------
# APPROVAL EXECUTION ENDPOINTS
# ----------------------------------------------------
from app.schemas.product_recommendation_rule import QuoteRecommendationRead
from app.schemas.quote_approval import ApprovalDecisionRequest, QuoteApprovalStepRead, QuoteSubmissionResponse
from app.schemas.what_if import WhatIfRequest, WhatIfResponse
from app.services.quote_approval import QuoteApprovalService


@router.post(
    "/{quotation_id}/submit",
    response_model=QuoteSubmissionResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Quotation for Automatic Approval Routing",
)
async def submit_quotation(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> QuoteSubmissionResponse:
    service = QuoteApprovalService(db)
    try:
        return await service.submit_quotation(quotation_id, current_user)
    except QuoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuoteNotEditableError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except QuotationValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{quotation_id}/approvals",
    response_model=List[QuoteApprovalStepRead],
    status_code=status.HTTP_200_OK,
    summary="Get Quotation Approval Steps & Triggers",
)
async def get_quotation_approvals(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
) -> List[QuoteApprovalStepRead]:
    service = QuoteApprovalService(db)
    try:
        steps = await service.list_approval_steps(quotation_id)
        return [QuoteApprovalStepRead.model_validate(s) for s in steps]
    except QuoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{quotation_id}/approvals/{step_id}/approve",
    response_model=QuotationRead,
    status_code=status.HTTP_200_OK,
    summary="Approve Quotation Approval Step",
)
async def approve_step(
    quotation_id: int,
    step_id: int,
    body: Optional[ApprovalDecisionRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMIN, RoleName.SALES_MANAGER, RoleName.FINANCE_OPERATIONS)),
) -> QuotationRead:
    service = QuoteApprovalService(db)
    try:
        reason = body.reason if body else None
        return await service.process_decision(quotation_id, step_id, "APPROVE", reason, current_user)
    except (QuoteNotFoundError, ResourceNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuoteNotEditableError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except QuotationValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{quotation_id}/approvals/{step_id}/reject",
    response_model=QuotationRead,
    status_code=status.HTTP_200_OK,
    summary="Reject Quotation Approval Step",
)
async def reject_step(
    quotation_id: int,
    step_id: int,
    body: ApprovalDecisionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMIN, RoleName.SALES_MANAGER, RoleName.FINANCE_OPERATIONS)),
) -> QuotationRead:
    service = QuoteApprovalService(db)
    try:
        return await service.process_decision(quotation_id, step_id, "REJECT", body.reason, current_user)
    except (QuoteNotFoundError, ResourceNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuoteNotEditableError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except QuotationValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{quotation_id}/approvals/{step_id}/return",
    response_model=QuotationRead,
    status_code=status.HTTP_200_OK,
    summary="Return Quotation for Revision",
)
async def return_step(
    quotation_id: int,
    step_id: int,
    body: ApprovalDecisionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMIN, RoleName.SALES_MANAGER, RoleName.FINANCE_OPERATIONS)),
) -> QuotationRead:
    service = QuoteApprovalService(db)
    try:
        return await service.process_decision(quotation_id, step_id, "RETURN", body.reason, current_user)
    except (QuoteNotFoundError, ResourceNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuoteNotEditableError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except QuotationValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ----------------------------------------------------
# UPSELL & RECOMMENDATION ENDPOINTS
# ----------------------------------------------------
@router.get(
    "/{quotation_id}/recommendations",
    response_model=List[QuoteRecommendationRead],
    status_code=status.HTTP_200_OK,
    summary="Get Ranked Upsell / Cross-Sell Recommendations for Quotation",
)
async def get_quotation_recommendations(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
) -> List[QuoteRecommendationRead]:
    service = QuotationService(db)
    try:
        recs = await service.get_recommendations(quotation_id)
        return [QuoteRecommendationRead.model_validate(r) for r in recs]
    except QuoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{quotation_id}/recommendations/{rule_id}/add",
    response_model=QuotationRead,
    status_code=status.HTTP_200_OK,
    summary="Add Upsell Recommendation to Quotation",
)
async def add_recommendation_to_quote(
    quotation_id: int,
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> QuotationRead:
    service = QuotationService(db)
    try:
        return await service.add_recommendation_to_quotation(quotation_id, rule_id, current_user)
    except (QuoteNotFoundError, ResourceNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuoteNotEditableError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except (CurrencyMismatchError, InactiveReferenceError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{quotation_id}/recommendations/{rule_id}/dismiss",
    response_model=QuotationRead,
    status_code=status.HTTP_200_OK,
    summary="Dismiss Recommendation for Quotation",
)
async def dismiss_recommendation(
    quotation_id: int,
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> QuotationRead:
    service = QuotationService(db)
    try:
        return await service.dismiss_recommendation(quotation_id, rule_id, current_user)
    except (QuoteNotFoundError, ResourceNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuoteNotEditableError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ----------------------------------------------------
# WHAT-IF SIMULATOR ENDPOINT (NON-PERSISTENT)
# ----------------------------------------------------
@router.post(
    "/{quotation_id}/what-if",
    response_model=WhatIfResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate Non-Persistent What-If Quotation Overrides",
)
async def run_what_if_simulation(
    quotation_id: int,
    body: WhatIfRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
) -> WhatIfResponse:
    service = QuotationService(db)
    try:
        res = await service.run_what_if_simulation(quotation_id, body)
        return WhatIfResponse.model_validate(res)
    except QuoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

