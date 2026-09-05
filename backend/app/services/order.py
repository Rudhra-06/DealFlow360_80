from datetime import datetime, timezone
import secrets
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import QuotationStatus
from app.models.order_audit_event import OrderAuditEvent
from app.models.sales_order import SalesOrder
from app.models.sales_order_line import SalesOrderLine
from app.repositories.quotation import QuotationRepository
from app.repositories.quote_version import QuoteVersionRepository
from app.repositories.sales_order import SalesOrderRepository
from app.services.exceptions import (
    ConfirmedVersionMissingError,
    OrderAlreadyExistsError,
    QuoteNotFoundError,
    ResourceNotFoundError,
)


class OrderService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.order_repo = SalesOrderRepository()
        self.quote_repo = QuotationRepository()
        self.version_repo = QuoteVersionRepository()

    def _generate_order_number(self) -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        rand_suffix = secrets.token_hex(4).upper()
        return f"SO-{date_str}-{rand_suffix}"

    async def ensure_order_for_confirmed_quote(
        self, quotation_id: int, actor_user_id: Optional[int] = None
    ) -> SalesOrder:
        """
        Idempotently converts a CUSTOMER_CONFIRMED quotation into a SalesOrder.
        If an order already exists for this quotation, returns the existing SalesOrder.
        """
        existing = await self.order_repo.get_by_quotation_id(self.db, quotation_id)
        if existing:
            return existing

        quote = await self.quote_repo.get_by_id(self.db, quotation_id)
        if not quote:
            raise QuoteNotFoundError(f"Quotation with ID {quotation_id} not found.")

        if quote.status != QuotationStatus.CUSTOMER_CONFIRMED.value and quote.status != QuotationStatus.CUSTOMER_ACCEPTED.value:
            raise ConfirmedVersionMissingError(
                f"Cannot create order for quotation {quotation_id} because status is '{quote.status}' (expected CUSTOMER_CONFIRMED)."
            )

        v_id = quote.confirmed_quote_version_id or quote.current_version_id
        if not v_id:
            versions = await self.version_repo.list_versions(self.db, quotation_id)
            if not versions:
                raise ConfirmedVersionMissingError(f"No version snapshot found for quotation {quotation_id}.")
            v_id = versions[-1].id

        confirmed_version = await self.version_repo.get_by_id(self.db, v_id)
        if not confirmed_version:
            raise ConfirmedVersionMissingError(f"Confirmed QuoteVersion ID {v_id} not found.")

        try:
            order = SalesOrder(
                order_number=self._generate_order_number(),
                quotation_id=quote.id,
                confirmed_quote_version_id=confirmed_version.id,
                customer_id=quote.customer_id,
                sales_rep_id=quote.sales_rep_id,
                status="FULFILLMENT",
                currency=confirmed_version.currency,
                payment_terms_days=confirmed_version.payment_terms_days,
                gross_subtotal=confirmed_version.gross_subtotal,
                discount_amount=confirmed_version.discount_amount,
                net_total=confirmed_version.net_total,
                total_cost=confirmed_version.total_cost,
                margin_amount=confirmed_version.margin_amount,
                margin_pct=confirmed_version.margin_pct,
                customer_confirmed_at=quote.customer_confirmed_at or datetime.now(timezone.utc),
            )

            for vl in confirmed_version.lines:
                # Classify billing type based on billing plan if assigned
                b_type = "ONE_TIME"
                if vl.billing_plan and vl.billing_plan.billing_type == "RECURRING":
                    b_type = "RECURRING"

                so_line = SalesOrderLine(
                    source_quote_line_id=vl.original_quote_line_id,
                    source_quote_version_line_id=vl.id,
                    product_id=vl.product_id,
                    billing_plan_id=vl.billing_plan_id,
                    product_sku_snapshot=vl.product_sku_snapshot,
                    product_name_snapshot=vl.product_name_snapshot,
                    product_description_snapshot=None,
                    quantity=vl.quantity,
                    unit_list_price=vl.unit_list_price,
                    unit_cost=vl.unit_cost,
                    line_discount_pct=vl.line_discount_pct,
                    effective_discount_pct=vl.effective_discount_pct,
                    gross_line_total=vl.gross_line_total,
                    discount_amount=vl.discount_amount,
                    net_line_total=vl.net_line_total,
                    line_cost=vl.line_cost,
                    margin_amount=vl.margin_amount,
                    margin_pct=vl.margin_pct,
                    billing_type=b_type,
                )
                order.lines.append(so_line)

            await self.order_repo.create_order(self.db, order)

            # Audit event
            audit = OrderAuditEvent(
                sales_order_id=order.id,
                actor_user_id=actor_user_id,
                event_type="ORDER_CREATED",
                to_status="FULFILLMENT",
                event_metadata={
                    "quotation_id": quote.id,
                    "quote_number": quote.quote_number,
                    "confirmed_version_id": confirmed_version.id,
                    "version_number": confirmed_version.version_number,
                },
            )
            self.db.add(audit)
            await self.db.flush()

            return await self.order_repo.get_by_id(self.db, order.id)
        except Exception:
            await self.db.rollback()
            raise

    async def create_order_from_confirmed_quotation(
        self, quotation_id: int, actor_user_id: Optional[int] = None
    ) -> SalesOrder:
        return await self.ensure_order_for_confirmed_quote(quotation_id, actor_user_id)

    async def get_order_by_id(self, order_id: int) -> SalesOrder:
        order = await self.order_repo.get_by_id(self.db, order_id)
        if not order:
            raise ResourceNotFoundError(f"SalesOrder with ID {order_id} not found.")
        return order

    async def get_order_by_quotation_id(self, quotation_id: int) -> SalesOrder:
        order = await self.order_repo.get_by_quotation_id(self.db, quotation_id)
        if not order:
            raise ResourceNotFoundError(f"SalesOrder for quotation ID {quotation_id} not found.")
        return order

    async def get_order_by_quotation(self, quotation_id: int) -> Optional[SalesOrder]:
        """Canonical public method to get sales order by quotation ID."""
        return await self.order_repo.get_by_quotation_id(self.db, quotation_id)

    async def list_orders(
        self,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        sales_rep_id: Optional[int] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SalesOrder]:
        return await self.order_repo.list_orders(
            self.db,
            status=status,
            customer_id=customer_id,
            sales_rep_id=sales_rep_id,
            search=search,
            limit=limit,
            offset=offset,
        )
