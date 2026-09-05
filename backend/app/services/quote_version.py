from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AuditEventType
from app.engines.version_diff import VersionDiffEngine
from app.models.quote_audit_event import QuoteAuditEvent
from app.models.quote_version import QuoteVersion
from app.models.quote_version_line import QuoteVersionLine
from app.repositories.quotation import QuotationRepository
from app.repositories.quote_version import QuoteVersionRepository
from app.schemas.quote_version import QuoteVersionCompareResult
from app.services.exceptions import QuoteNotFoundError, ResourceNotFoundError


class QuoteVersionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.quote_repo = QuotationRepository()
        self.version_repo = QuoteVersionRepository()

    async def create_version_snapshot(
        self,
        quotation_id: int,
        source_type: str,
        created_by_user_id: Optional[int] = None,
        source_negotiation_request_id: Optional[int] = None,
        approval_status: str = "APPROVED",
    ) -> QuoteVersion:
        # 1. Lock quote row and calculate next version number safely
        quote = await self.quote_repo.get_by_id(self.db, quotation_id)
        if not quote:
            raise QuoteNotFoundError(f"Quotation with ID {quotation_id} not found.")

        next_version = await self.version_repo.get_next_version_number_with_lock(self.db, quotation_id)

        # 2. Build QuoteVersion snapshot
        version = QuoteVersion(
            quotation_id=quote.id,
            version_number=next_version,
            source_type=source_type,
            created_by_user_id=created_by_user_id,
            status_snapshot=quote.status,
            approval_status=approval_status,
            currency=quote.currency,
            payment_terms_days=quote.payment_terms_days,
            order_discount_pct=quote.order_discount_pct,
            gross_subtotal=quote.gross_subtotal,
            discount_amount=quote.discount_amount,
            net_total=quote.net_total,
            total_cost=quote.total_cost,
            margin_amount=quote.margin_amount,
            margin_pct=quote.margin_pct,
            weighted_effective_discount_pct=quote.weighted_effective_discount_pct,
            blended_risk_score=quote.blended_risk_score,
            risk_level=quote.risk_level,
            source_negotiation_request_id=source_negotiation_request_id,
        )

        # 3. Snapshot Quote Version Lines
        for line in quote.lines:
            v_line = QuoteVersionLine(
                original_quote_line_id=line.id,
                product_id=line.product_id,
                billing_plan_id=line.billing_plan_id,
                product_sku_snapshot=line.product.sku if line.product else "N/A",
                product_name_snapshot=line.product.name if line.product else "N/A",
                quantity=line.quantity,
                unit_list_price=line.unit_list_price,
                unit_cost=line.unit_cost,
                line_discount_pct=line.line_discount_pct,
                effective_discount_pct=line.effective_discount_pct,
                gross_line_total=line.gross_line_total,
                discount_amount=line.discount_amount,
                net_line_total=line.net_line_total,
                line_cost=line.line_cost,
                margin_amount=line.margin_amount,
                margin_pct=line.margin_pct,
                standard_discount_pct_snapshot=line.standard_discount_pct_snapshot,
                max_discount_pct_snapshot=line.max_discount_pct_snapshot,
                risk_level=line.risk_level,
                source_type=line.source_type,
            )
            version.lines.append(v_line)

        await self.version_repo.create_version(self.db, version)

        # Update quotation state references
        quote.current_version_id = version.id
        if approval_status == "APPROVED":
            quote.latest_approved_version_id = version.id

        # Audit Event
        audit = QuoteAuditEvent(
            quotation_id=quote.id,
            actor_user_id=created_by_user_id,
            event_type=AuditEventType.QUOTE_VERSION_CREATED.value,
            to_status=quote.status,
            event_metadata={
                "version_number": next_version,
                "source_type": source_type,
                "approval_status": approval_status,
            },
        )
        self.db.add(audit)
        await self.db.flush()

        return await self.version_repo.get_by_id(self.db, version.id)

    async def get_versions(self, quotation_id: int) -> List[QuoteVersion]:
        quote = await self.quote_repo.get_by_id(self.db, quotation_id)
        if not quote:
            raise QuoteNotFoundError(f"Quotation with ID {quotation_id} not found.")
        return await self.version_repo.list_versions(self.db, quotation_id)

    async def get_version_by_number(self, quotation_id: int, version_number: int) -> QuoteVersion:
        version = await self.version_repo.get_by_number(self.db, quotation_id, version_number)
        if not version:
            raise ResourceNotFoundError(f"QuoteVersion v{version_number} not found for quotation ID {quotation_id}.")
        return version

    async def compare_versions(
        self, quotation_id: int, from_version_number: int, to_version_number: int
    ) -> QuoteVersionCompareResult:
        v_from = await self.get_version_by_number(quotation_id, from_version_number)
        v_to = await self.get_version_by_number(quotation_id, to_version_number)
        return VersionDiffEngine.compare_versions(v_from, v_to)
