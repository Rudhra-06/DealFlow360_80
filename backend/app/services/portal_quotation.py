from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AuditEventType, NotificationType, QuotationStatus
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
        QuotationStatus.SENT_TO_CUSTOMER.value,
        QuotationStatus.UNDER_CUSTOMER_REVIEW.value,
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

    async def _verify_customer_ownership(self, quotation_id: int, user_id: int) -> Quotation:
        customer_id = await self.portal_access_service.get_active_customer_id_for_user(user_id)
        quote = await self.quote_repo.get_by_id(self.db, quotation_id)
        if not quote:
            raise QuoteNotFoundError(f"Quotation with ID {quotation_id} not found.")

        if quote.customer_id != customer_id:
            raise QuoteAccessDeniedError("Access denied to customer portal quotation.")

        return quote

    async def list_portal_quotations(
        self, user_id: int, status: Optional[str] = None
    ) -> List[Quotation]:
        customer_id = await self.portal_access_service.get_active_customer_id_for_user(user_id)
        quotes = await self.quote_repo.list_quotations(self.db, customer_id=customer_id)

        # Filter out internal/draft quotes that have not been sent to customer
        filtered_quotes = [q for q in quotes if q.status in self.ALLOWED_PORTAL_STATUSES]
        if status:
            filtered_quotes = [q for q in filtered_quotes if q.status == status]

        return filtered_quotes

    async def get_portal_quotation(self, quotation_id: int, user_id: int) -> Quotation:
        quote = await self._verify_customer_ownership(quotation_id, user_id)
        if quote.status not in self.ALLOWED_PORTAL_STATUSES:
            raise QuoteAccessDeniedError("Quotation is not available for customer review.")
        return quote

    async def list_portal_versions(self, quotation_id: int, user_id: int) -> List[QuoteVersion]:
        await self._verify_customer_ownership(quotation_id, user_id)
        return await self.version_repo.list_versions(self.db, quotation_id)

    async def get_portal_version(
        self, quotation_id: int, version_number: int, user_id: int
    ) -> QuoteVersion:
        await self._verify_customer_ownership(quotation_id, user_id)
        version = await self.version_repo.get_by_number(self.db, quotation_id, version_number)
        if not version:
            raise ResourceNotFoundError(
                f"QuoteVersion v{version_number} not found for quotation ID {quotation_id}."
            )
        return version

    async def compare_portal_versions(
        self, quotation_id: int, from_v: int, to_v: int, user_id: int
    ):
        await self._verify_customer_ownership(quotation_id, user_id)
        return await self.version_service.compare_versions(quotation_id, from_v, to_v)

    async def confirm_quotation(self, quotation_id: int, user_id: int) -> Quotation:
        quote = await self._verify_customer_ownership(quotation_id, user_id)

        if quote.status not in (
            QuotationStatus.SENT_TO_CUSTOMER.value,
            QuotationStatus.UNDER_CUSTOMER_REVIEW.value,
        ):
            raise CommercialPolicyValidationError(
                f"Quotation cannot be confirmed in state '{quote.status}'."
            )

        current_v_id = quote.current_version_id
        if not current_v_id:
            # Fallback to latest version snapshot if current_version_id is not set
            versions = await self.version_repo.list_versions(self.db, quotation_id)
            if versions:
                current_v_id = versions[-1].id

        from_status = quote.status
        quote.confirmed_quote_version_id = current_v_id
        quote.customer_confirmed_at = datetime.now(timezone.utc)
        quote.customer_confirmed_by_user_id = user_id
        quote.status = QuotationStatus.CUSTOMER_ACCEPTED.value

        # Audit logging
        audit = QuoteAuditEvent(
            quotation_id=quote.id,
            actor_user_id=user_id,
            event_type=AuditEventType.CUSTOMER_CONFIRMED.value,
            from_status=from_status,
            to_status=QuotationStatus.CUSTOMER_ACCEPTED.value,
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
            await self.db.commit()
            quote_result = await self.quote_repo.get_by_id(self.db, quotation_id)
        except Exception:
            await self.db.rollback()
            raise

        # Post-commit notifications
        if quote_result.sales_rep_id:
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

        return quote_result
