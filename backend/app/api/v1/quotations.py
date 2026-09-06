from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.rbac import require_roles
from app.core.enums import RoleName
from app.db.session import get_db
from app.models.user import User
from app.schemas.reports import ReportExportFormat, ReportExportRequest, ReportTypeEnum
from app.services.report_export import ReportExportService
from app.schemas.quote_audit_event import QuoteAuditEventRead
from app.schemas.quotation import (
    QuotationCreate,
    QuotationListItem,
    QuotationRead,
    QuotationUpdate,
    QuoteRecalculationRead,
)
from app.schemas.quotation_line import QuoteLineCreate, QuoteLineUpdate
from app.schemas.quote_negotiation import (
    QuoteNegotiationMessageCreate,
    QuoteNegotiationMessageRead,
    QuoteNegotiationRequestRead,
    QuoteNegotiationRequestReject,
)
from app.schemas.quote_version import QuoteVersionCompareResult, QuoteVersionRead
from app.services.exceptions import (
    CommercialPolicyValidationError,
    CurrencyMismatchError,
    InactiveReferenceError,
    InvalidReferenceError,
    QuoteAccessDeniedError,
    QuoteLineNotFoundError,
    QuoteNotEditableError,
    QuoteNotFoundError,
    QuotationValidationError,
    ResourceNotFoundError,
)
from app.services.quote_negotiation import QuoteNegotiationService
from app.services.quote_version import QuoteVersionService
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
    RoleName.SALES_MANAGER,
    RoleName.FINANCE_OPERATIONS,
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
        return [QuoteRecommendationRead.model_validate(r.model_dump()) for r in recs]
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
        return WhatIfResponse.model_validate(res.model_dump())
    except QuoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ----------------------------------------------------
# PHASE 4: SEND TO CUSTOMER, VERSIONING & NEGOTIATION
# ----------------------------------------------------
@router.post(
    "/{quotation_id}/send-to-customer",
    response_model=QuotationRead,
    status_code=status.HTTP_200_OK,
    summary="Send Approved Quotation to Customer",
)
async def send_quotation_to_customer(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
) -> QuotationRead:
    service = QuotationService(db)
    try:
        return await service.send_to_customer(quotation_id, current_user)
    except QuoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except CommercialPolicyValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{quotation_id}/pdf",
    summary="Export Individual Quotation as PDF Document",
)
async def export_quotation_pdf(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = ReportExportService(db)
    req = ReportExportRequest(
        report_type=ReportTypeEnum.QUOTATION,
        format=ReportExportFormat.PDF,
        quotation_id=quotation_id,
    )
    file_bytes, filename, mime_type = await service.export_report(req, current_user)
    return Response(
        content=file_bytes,
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get(
    "/{quotation_id}/versions",
    response_model=List[QuoteVersionRead],
    summary="List Internal Quotation Version Snapshots",
)
async def list_quote_versions(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
):
    service = QuoteVersionService(db)
    try:
        versions = await service.get_versions(quotation_id)
        return [QuoteVersionRead.model_validate(v) for v in versions]
    except QuoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{quotation_id}/versions/compare",
    response_model=QuoteVersionCompareResult,
    summary="Compare Internal Quotation Versions",
)
async def compare_quote_versions(
    quotation_id: int,
    from_version: int = Query(..., ge=1),
    to_version: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
):
    service = QuoteVersionService(db)
    try:
        return await service.compare_versions(quotation_id, from_version, to_version)
    except (QuoteNotFoundError, ResourceNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{quotation_id}/versions/{version_number}",
    response_model=QuoteVersionRead,
    summary="Get Specific Quotation Version Snapshot",
)
async def get_quote_version(
    quotation_id: int,
    version_number: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
):
    service = QuoteVersionService(db)
    try:
        version = await service.get_version_by_number(quotation_id, version_number)
        return QuoteVersionRead.model_validate(version)
    except (QuoteNotFoundError, ResourceNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{quotation_id}/negotiation-inbox",
    response_model=List[QuoteNegotiationRequestRead],
    summary="Sales Rep Negotiation Requests Inbox",
)
async def get_quote_negotiation_inbox(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES)),
):
    service = QuoteNegotiationService(db)
    try:
        reqs = await service.get_negotiation_inbox(quotation_id)
        return [QuoteNegotiationRequestRead.model_validate(r) for r in reqs]
    except QuoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{quotation_id}/negotiation-requests/{request_id}/accept",
    response_model=QuotationRead,
    summary="Sales Rep Accepts Customer Counter-Offer / Negotiation Request",
)
async def accept_customer_negotiation_request(
    quotation_id: int,
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
):
    service = QuoteNegotiationService(db)
    try:
        return await service.accept_negotiation_request(quotation_id, request_id, current_user)
    except (QuoteNotFoundError, ResourceNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CommercialPolicyValidationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post(
    "/{quotation_id}/negotiation-requests/{request_id}/reject",
    response_model=QuoteNegotiationRequestRead,
    summary="Sales Rep Rejects Customer Counter-Offer",
)
async def reject_customer_negotiation_request(
    quotation_id: int,
    request_id: int,
    obj_in: QuoteNegotiationRequestReject,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
):
    service = QuoteNegotiationService(db)
    try:
        req = await service.reject_negotiation_request(quotation_id, request_id, obj_in, current_user)
        return QuoteNegotiationRequestRead.model_validate(req)
    except (QuoteNotFoundError, ResourceNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CommercialPolicyValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post(
    "/{quotation_id}/messages",
    response_model=QuoteNegotiationMessageRead,
    status_code=status.HTTP_201_CREATED,
    summary="Sales Rep Replies to Customer Message / Comment",
)
async def reply_internal_message(
    quotation_id: int,
    obj_in: QuoteNegotiationMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
):
    service = QuoteNegotiationService(db)
    try:
        msg = await service.add_internal_message(quotation_id, obj_in, current_user)
        return QuoteNegotiationMessageRead.model_validate(msg)
    except QuoteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuoteAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get(
    "/{quotation_id}/pdf",
    summary="Export quotation PDF document",
)
async def export_quotation_pdf(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = ReportExportService(db)
    req = ReportExportRequest(
        report_type=ReportTypeEnum.QUOTATION,
        format=ReportExportFormat.PDF,
        quotation_id=quotation_id,
    )
    pdf_bytes, filename, mime_type = await service.export_report(req, current_user)
    return Response(
        content=pdf_bytes,
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


