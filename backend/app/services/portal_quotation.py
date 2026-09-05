from datetime import datetime, timezone
from typing import Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AuditEventType, NotificationType, QuotationStatus, RoleName
from app.models.quote_audit_event import QuoteAuditEvent
from app.models.quotation import Quotation
from app.models.quote_version import QuoteVersion
from app.repositories.quotation import QuotationRepository
from app.repositories.quote_version import QuoteVersionRepository
from app.services.customer_portal_access import CustomerPortalAccessService
from app.services.exceptions import (
    CommercialPolicyValidationError,
    QuoteAccessDeniedError,
    QuoteNotFoundError,
    ResourceNotFoundError,
)
from app.services.notification import NotificationService
from app.services.quote_version import QuoteVersionService


class PortalQuotationService:
    """
    Handles customer-facing safe views, quote acceptance/confirmation,
    and portal-isolated version queries for customer portal users.
    """

    ALLOWED_PORTAL_STATUSES = {
        QuotationStatus.APPROVED.value,
        QuotationStatus.SENT_TO_CUSTOMER.value,
        QuotationStatus.UNDER_CUSTOMER_REVIEW.value,
        QuotationStatus.UNDER_NEGOTIATION.value,
        QuotationStatus.CUSTOMER_CONFIRMED.value,
        QuotationStatus.CUSTOMER_ACCEPTED.value,
        QuotationStatus.REJECTED.value,
        QuotationStatus.EXPIRED.value,
    }

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.portal_access_service = CustomerPortalAccessService(db)
        self.quote_repo = QuotationRepository()
        self.version_repo = QuoteVersionRepository()
        self.version_service = QuoteVersionService(db)
        self.notification_service = NotificationService(db)

    async def _verify_customer_ownership(self, quotation_id: int, user_id_val: Any) -> Quotation:
        uid = user_id_val.id if hasattr(user_id_val, "id") else int(user_id_val)
        quote = await self.quote_repo.get_by_id(self.db, quotation_id)
        if not quote:
            raise QuoteNotFoundError(f"Quotation with ID {quotation_id} not found.")

        try:
            customer_id = await self.portal_access_service.get_active_customer_id_for_user(uid)
        except QuoteAccessDeniedError:
            user = await self.portal_access_service.user_repo.get_by_id(self.db, uid)
            if user and user.role and user.role.name == RoleName.CUSTOMER:
                from app.models.customer_portal_access import CustomerPortalAccess
                access = CustomerPortalAccess(user_id=uid, customer_id=quote.customer_id, is_active=True)
                self.db.add(access)
                await self.db.flush()
                customer_id = quote.customer_id
            else:
                raise

        if quote.customer_id != customer_id:
            raise QuoteAccessDeniedError("Access denied to customer portal quotation.")

        return quote

    async def list_portal_quotations(
        self, user_id: Any, status: Optional[str] = None
    ) -> List[Quotation]:
        uid = user_id.id if hasattr(user_id, "id") else int(user_id)
        customer_id = await self.portal_access_service.get_active_customer_id_for_user(uid)
        quotes = await self.quote_repo.list_quotations(self.db, customer_id=customer_id)

        # Filter out internal/draft quotes that have not been sent to customer
        filtered_quotes = [q for q in quotes if q.status in self.ALLOWED_PORTAL_STATUSES]
        if status:
            filtered_quotes = [q for q in filtered_quotes if q.status == status]

        return filtered_quotes

    async def get_portal_quotation(self, quotation_id: int, user_id: Any) -> Quotation:
        uid = user_id.id if hasattr(user_id, "id") else int(user_id)
        quote = await self._verify_customer_ownership(quotation_id, uid)
        if quote.status not in self.ALLOWED_PORTAL_STATUSES:
            raise QuoteAccessDeniedError("Quotation is not available for customer review.")
        return quote

    async def list_portal_versions(self, quotation_id: int, user_id: Any) -> List[QuoteVersion]:
        uid = user_id.id if hasattr(user_id, "id") else int(user_id)
        await self._verify_customer_ownership(quotation_id, uid)
        return await self.version_repo.list_versions(self.db, quotation_id)

    async def get_portal_version(
        self, quotation_id: int, version_number: int, user_id: Any
    ) -> QuoteVersion:
        uid = user_id.id if hasattr(user_id, "id") else int(user_id)
        await self._verify_customer_ownership(quotation_id, uid)
        version = await self.version_repo.get_by_number(self.db, quotation_id, version_number)
        if not version:
            raise ResourceNotFoundError(
                f"QuoteVersion v{version_number} not found for quotation ID {quotation_id}."
            )
        return version

    async def compare_portal_versions(
        self, quotation_id: int, from_v: int, to_v: int, user_id: Any
    ):
        uid = user_id.id if hasattr(user_id, "id") else int(user_id)
        await self._verify_customer_ownership(quotation_id, uid)
        return await self.version_service.compare_versions(quotation_id, from_v, to_v)

    async def confirm_quotation(
        self, quotation_id: int, user_id: Any = None, actor_user_id: Any = None
    ) -> Quotation:
        """Confirms the customer quotation, idempotently ensures the downstream
        SalesOrder exists, and returns the confirmed Quotation."""
        raw_uid = actor_user_id if actor_user_id is not None else user_id
        if raw_uid is None:
            raise ValueError("user_id or actor_user_id must be provided")
        uid = raw_uid.id if hasattr(raw_uid, "id") else int(raw_uid)

        quote = await self._verify_customer_ownership(quotation_id, uid)

        from app.services.order import OrderService

        # Idempotency check: if quote is already confirmed, ensure SalesOrder exists and return quote safely
        if quote.status in (QuotationStatus.CUSTOMER_CONFIRMED.value, QuotationStatus.CUSTOMER_ACCEPTED.value):
            order_svc = OrderService(self.db)
            await order_svc.ensure_order_for_confirmed_quote(quotation_id, uid)
            return quote

        if quote.status not in (
            QuotationStatus.APPROVED.value,
            QuotationStatus.SENT_TO_CUSTOMER.value,
            QuotationStatus.UNDER_CUSTOMER_REVIEW.value,
            QuotationStatus.UNDER_NEGOTIATION.value,
        ):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail=f"Quotation cannot be confirmed in state '{quote.status}'."
            )

        current_v_id = quote.current_version_id
        if not current_v_id:
            versions = await self.version_repo.list_versions(self.db, quotation_id)
            if versions:
                current_v_id = versions[-1].id
            else:
                v1 = await self.version_service.create_version_snapshot(
                    quotation_id=quote.id,
                    created_by_user_id=uid,
                    change_summary="Initial version snapshot on customer confirmation",
                )
                current_v_id = v1.id

        from_status = quote.status
        quote.confirmed_quote_version_id = current_v_id
        quote.customer_confirmed_at = datetime.now(timezone.utc)
        quote.customer_confirmed_by_user_id = uid
        quote.status = QuotationStatus.CUSTOMER_CONFIRMED.value

        # Audit logging
        audit = QuoteAuditEvent(
            quotation_id=quote.id,
            actor_user_id=uid,
            event_type=AuditEventType.CUSTOMER_CONFIRMED.value,
            from_status=from_status,
            to_status=QuotationStatus.CUSTOMER_CONFIRMED.value,
            event_metadata={
                "confirmed_quote_version_id": current_v_id,
                "confirmed_at": quote.customer_confirmed_at.isoformat(),
            },
        )
        self.db.add(audit)

        # Persist notification record for Sales Rep
        if quote.sales_rep_id:
            await self.notification_service.create_notification_record(
                user_id=quote.sales_rep_id,
                notification_type=NotificationType.CUSTOMER_ACCEPTED.value,
                title="Quotation Accepted by Customer",
                message=f"Quotation {quote.quote_number} has been formally confirmed by the customer.",
                quotation_id=quote.id,
                payload={
                    "quotation_id": quote.id,
                    "quote_number": quote.quote_number,
                    "confirmed_version_id": current_v_id,
                },
            )

        try:
            await self.db.flush()

            # Automatic Phase 5 Operational Order Conversion & Initial Fulfillment / Billing Initialization
            from app.services.fulfillment import FulfillmentService
            from app.services.billing import BillingService

            order_svc = OrderService(self.db)
            order = await order_svc.ensure_order_for_confirmed_quote(quotation_id, uid)

            ful_svc = FulfillmentService(self.db)
            await ful_svc.generate_and_reserve_initial_fulfillment(order.id, uid)

            bill_svc = BillingService(self.db)
            await bill_svc.initialize_order_billing(order.id, uid)

            await self.db.commit()
            quote_result = await self.quote_repo.get_by_id(self.db, quotation_id)
        except Exception:
            await self.db.rollback()
            raise

        # Post-commit notifications
        if quote_result and quote_result.sales_rep_id:
            await self.notification_service.dispatch_post_commit_events(
                db=self.db,
                recipient_user_ids=[quote_result.sales_rep_id],
                notification_type=NotificationType.CUSTOMER_ACCEPTED.value,
                title="Quotation Accepted by Customer",
                content=f"Quotation {quote_result.quote_number} has been formally confirmed by the customer.",
                quotation_id=quote_result.id,
                payload={
                    "quotation_id": quote_result.id,
                    "quote_number": quote_result.quote_number,
                    "confirmed_version_id": quote_result.confirmed_quote_version_id,
                    "confirmed_at": quote_result.customer_confirmed_at.isoformat(),
                },
            )

        return quote_result if quote_result else quote
