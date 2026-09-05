from datetime import datetime, timedelta, timezone
import secrets
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession


def add_months(dt: datetime, months: int) -> datetime:
    """Utility to add months to a datetime without external dateutil dependency."""
    year = dt.year + (dt.month + months - 1) // 12
    month = (dt.month + months - 1) % 12 + 1
    max_days = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
    day = min(dt.day, max_days)
    return dt.replace(year=year, month=month, day=day)

from app.models.billing_schedule import BillingSchedule
from app.models.invoice import Invoice
from app.models.invoice_line import InvoiceLine
from app.models.order_audit_event import OrderAuditEvent
from app.models.sales_order import SalesOrder
from app.models.subscription import Subscription
from app.repositories.invoice import InvoiceRepository
from app.repositories.sales_order import SalesOrderRepository
from app.repositories.subscription import SubscriptionRepository
from app.services.exceptions import (
    BillingAlreadyInitializedError,
    ResourceNotFoundError,
)
from app.services.notification import NotificationService


class BillingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.order_repo = SalesOrderRepository()
        self.invoice_repo = InvoiceRepository()
        self.sub_repo = SubscriptionRepository()
        self.notif_service = NotificationService(db)

    def _generate_invoice_number(self) -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        rand_suffix = secrets.token_hex(4).upper()
        return f"INV-{date_str}-{rand_suffix}"

    def _generate_sub_number(self) -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        rand_suffix = secrets.token_hex(4).upper()
        return f"SUB-{date_str}-{rand_suffix}"

    async def initialize_order_billing(
        self, sales_order_id: int, actor_user_id: Optional[int] = None
    ) -> List[Invoice]:
        """
        ATOMIC IDEMPOTENT BILLING INITIALIZATION:
        1. Creates ONE_TIME invoice for non-recurring order lines.
        2. Creates Subscription + 12 monthly BillingSchedule entries for RECURRING lines.
        3. Issues first due recurring invoice.
        4. Updates order status to BILLED / ACTIVE_SUBSCRIPTION.
        """
        order = await self.order_repo.get_by_id(self.db, sales_order_id)
        if not order:
            raise ResourceNotFoundError(f"SalesOrder with ID {sales_order_id} not found.")

        existing_invoices = await self.invoice_repo.list_by_order(self.db, sales_order_id)
        if existing_invoices:
            return existing_invoices

        try:
            now = datetime.now(timezone.utc)
            one_time_lines = [l for l in order.lines if l.billing_type != "RECURRING"]
            recurring_lines = [l for l in order.lines if l.billing_type == "RECURRING"]

            created_invoices: List[Invoice] = []

            # 1. Process ONE_TIME billing lines
            if one_time_lines:
                subtotal = sum((l.gross_line_total for l in one_time_lines), 0)
                discount = sum((l.discount_amount for l in one_time_lines), 0)
                total = sum((l.net_line_total for l in one_time_lines), 0)

                due_date = now + timedelta(days=order.payment_terms_days)

                one_time_inv = Invoice(
                    invoice_number=self._generate_invoice_number(),
                    sales_order_id=order.id,
                    customer_id=order.customer_id,
                    invoice_type="ONE_TIME",
                    status="ISSUED",
                    currency=order.currency,
                    subtotal=subtotal,
                    tax_amount=0,
                    total_amount=total,
                    credited_amount=0,
                    paid_amount=0,
                    balance_due=total,
                    issue_date=now,
                    due_date=due_date,
                )

                for l in one_time_lines:
                    inv_line = InvoiceLine(
                        sales_order_line_id=l.id,
                        line_type="ONE_TIME",
                        description=f"{l.product_name_snapshot} (SKU: {l.product_sku_snapshot})",
                        quantity=l.quantity,
                        unit_price=l.unit_list_price,
                        amount=l.net_line_total,
                    )
                    one_time_inv.lines.append(inv_line)

                await self.invoice_repo.create_invoice(self.db, one_time_inv)
                created_invoices.append(one_time_inv)

            # 2. Process RECURRING lines (Create Subscriptions & BillingSchedules)
            has_active_sub = False
            for l in recurring_lines:
                has_active_sub = True
                plan = l.billing_plan
                interval = plan.billing_interval_months if (plan and plan.billing_interval_months) else 1
                proration = plan.proration_method if plan else "DAILY"
                cancel_method = plan.cancellation_method if plan else "END_OF_PERIOD"

                p_start = now
                p_end = add_months(now, interval)

                sub = Subscription(
                    subscription_number=self._generate_sub_number(),
                    sales_order_id=order.id,
                    sales_order_line_id=l.id,
                    customer_id=order.customer_id,
                    billing_plan_id=l.billing_plan_id or 1,
                    status="ACTIVE",
                    quantity=l.quantity,
                    unit_price=l.unit_list_price,
                    currency=order.currency,
                    interval_months=interval,
                    proration_method=proration,
                    cancellation_method=cancel_method,
                    start_date=p_start,
                    current_period_start=p_start,
                    current_period_end=p_end,
                    next_billing_date=p_end,
                )

                # Generate 12 future schedule entries
                for seq in range(1, 13):
                    seq_start = add_months(p_start, interval * (seq - 1))
                    seq_end = add_months(p_start, interval * seq)
                    sch_status = "SCHEDULED"

                    sch = BillingSchedule(
                        sequence=seq,
                        period_start=seq_start,
                        period_end=seq_end,
                        billing_date=seq_start,
                        scheduled_amount=l.net_line_total,
                        status=sch_status,
                    )
                    sub.schedules.append(sch)

                await self.sub_repo.create_subscription(self.db, sub)

                # Issue first recurring invoice for sequence 1 schedule
                first_sch = sub.schedules[0]
                rec_due_date = now + timedelta(days=order.payment_terms_days)

                rec_inv = Invoice(
                    invoice_number=self._generate_invoice_number(),
                    sales_order_id=order.id,
                    customer_id=order.customer_id,
                    invoice_type="RECURRING",
                    status="ISSUED",
                    currency=order.currency,
                    subtotal=l.gross_line_total,
                    tax_amount=0,
                    total_amount=l.net_line_total,
                    credited_amount=0,
                    paid_amount=0,
                    balance_due=l.net_line_total,
                    issue_date=now,
                    due_date=rec_due_date,
                    billing_period_start=first_sch.period_start,
                    billing_period_end=first_sch.period_end,
                )

                rec_inv_line = InvoiceLine(
                    sales_order_line_id=l.id,
                    subscription_id=sub.id,
                    line_type="RECURRING",
                    description=f"{l.product_name_snapshot} - Recurring Billing ({first_sch.period_start.strftime('%Y-%m-%d')} to {first_sch.period_end.strftime('%Y-%m-%d')})",
                    quantity=l.quantity,
                    unit_price=l.unit_list_price,
                    amount=l.net_line_total,
                    billing_period_start=first_sch.period_start,
                    billing_period_end=first_sch.period_end,
                )
                rec_inv.lines.append(rec_inv_line)

                await self.invoice_repo.create_invoice(self.db, rec_inv)
                created_invoices.append(rec_inv)

                first_sch.status = "INVOICED"
                first_sch.invoice_id = rec_inv.id

            # Update Order Status (only if physical fulfillment is complete or order has no physical lines)
            is_fulfillment_open = order.status in {"FULFILLMENT", "PARTIALLY_FULFILLED", "BACKORDERED"}
            if not is_fulfillment_open:
                if has_active_sub:
                    order.status = "ACTIVE_SUBSCRIPTION"
                else:
                    order.status = "BILLED"

            self.db.add(
                OrderAuditEvent(
                    sales_order_id=order.id,
                    actor_user_id=actor_user_id,
                    event_type="BILLING_INITIALIZED",
                    to_status=order.status,
                    event_metadata={"invoice_count": len(created_invoices)},
                )
            )

            await self.db.commit()
            return await self.invoice_repo.list_by_order(self.db, sales_order_id)
        except Exception:
            await self.db.rollback()
            raise

    async def generate_due_recurring_invoices(
        self, as_of_date: Optional[datetime] = None, actor_user_id: Optional[int] = None
    ) -> List[Invoice]:
        """
        Idempotent recurring billing engine execution.
        Finds all un-invoiced BillingSchedules where billing_date <= as_of_date, creates invoices,
        and links schedules.
        """
        cutoff = as_of_date or datetime.now(timezone.utc)
        due_schedules = await self.sub_repo.list_due_schedules(self.db, cutoff)

        if not due_schedules:
            return []

        created: List[Invoice] = []
        try:
            for sch in due_schedules:
                sub = sch.subscription
                if not sub or sub.status != "ACTIVE":
                    continue

                inv_due = cutoff + timedelta(days=30)
                inv = Invoice(
                    invoice_number=self._generate_invoice_number(),
                    sales_order_id=sub.sales_order_id,
                    customer_id=sub.customer_id,
                    invoice_type="RECURRING",
                    status="ISSUED",
                    currency=sub.currency,
                    subtotal=sch.scheduled_amount,
                    tax_amount=0,
                    total_amount=sch.scheduled_amount,
                    credited_amount=0,
                    paid_amount=0,
                    balance_due=sch.scheduled_amount,
                    issue_date=cutoff,
                    due_date=inv_due,
                    billing_period_start=sch.period_start,
                    billing_period_end=sch.period_end,
                )

                inv_line = InvoiceLine(
                    sales_order_line_id=sub.sales_order_line_id,
                    subscription_id=sub.id,
                    line_type="RECURRING",
                    description=f"Subscription {sub.subscription_number} Period ({sch.period_start.strftime('%Y-%m-%d')} to {sch.period_end.strftime('%Y-%m-%d')})",
                    quantity=sub.quantity,
                    unit_price=sub.unit_price,
                    amount=sch.scheduled_amount,
                    billing_period_start=sch.period_start,
                    billing_period_end=sch.period_end,
                )
                inv.lines.append(inv_line)

                await self.invoice_repo.create_invoice(self.db, inv)

                sch.status = "INVOICED"
                sch.invoice_id = inv.id
                sub.current_period_start = sch.period_start
                sub.current_period_end = sch.period_end
                sub.next_billing_date = sch.period_end

                created.append(inv)

            await self.db.commit()
            return created
        except Exception:
            await self.db.rollback()
            raise
