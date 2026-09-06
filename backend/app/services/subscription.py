from datetime import datetime, timezone
import secrets
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.proration import ProrationEngine
from app.models.credit_note import CreditNote
from app.models.credit_note_line import CreditNoteLine
from app.models.invoice import Invoice
from app.models.invoice_line import InvoiceLine
from app.models.order_audit_event import OrderAuditEvent
from app.models.subscription import Subscription
from app.repositories.credit_note import CreditNoteRepository
from app.repositories.invoice import InvoiceRepository
from app.repositories.subscription import SubscriptionRepository
from app.services.exceptions import (
    InvalidProrationDateError,
    ResourceNotFoundError,
    SubscriptionStateError,
)


class SubscriptionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.sub_repo = SubscriptionRepository()
        self.invoice_repo = InvoiceRepository()
        self.cn_repo = CreditNoteRepository()

    def _generate_cn_number(self) -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        rand_suffix = secrets.token_hex(4).upper()
        return f"CN-{date_str}-{rand_suffix}"

    def _generate_inv_number(self) -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        rand_suffix = secrets.token_hex(4).upper()
        return f"INV-{date_str}-{rand_suffix}"

    async def change_subscription_quantity(
        self,
        subscription_id: int,
        new_quantity: float,
        effective_date: Optional[datetime] = None,
        reason: Optional[str] = None,
        actor_user_id: Optional[int] = None,
    ) -> Subscription:
        """
        ATOMIC SUBSCRIPTION QUANTITY CHANGE:
        Calculates exact daily proration fraction for mid-cycle changes, issues PRORATION invoice/charge
        for quantity increases, or credit note for quantity decreases, and updates future schedule entries.
        """
        sub = await self.sub_repo.get_by_id(self.db, subscription_id)
        if not sub:
            raise ResourceNotFoundError(f"Subscription with ID {subscription_id} not found.")

        if sub.status != "ACTIVE":
            raise SubscriptionStateError(f"Cannot change quantity for subscription in '{sub.status}' status.")

        new_qty = float(new_quantity)
        if new_qty <= 0:
            raise SubscriptionStateError("Subscription quantity must be greater than zero.")

        eff_date = effective_date or datetime.now(timezone.utc)
        old_qty = sub.quantity

        try:
            # 1. Run ProrationEngine
            pro_res = ProrationEngine.calculate_mid_cycle_proration(
                period_start=sub.current_period_start,
                period_end=sub.current_period_end,
                effective_date=eff_date,
                old_quantity=old_qty,
                new_quantity=new_qty,
                unit_price=sub.unit_price,
                proration_method=sub.proration_method,
            )

            # 2. Issue proration charge/credit invoice or credit note
            if pro_res.prorated_amount > 0:
                # Quantity increase -> issue PRORATION invoice
                inv = Invoice(
                    invoice_number=self._generate_inv_number(),
                    sales_order_id=sub.sales_order_id,
                    customer_id=sub.customer_id,
                    invoice_type="PRORATION",
                    status="ISSUED",
                    currency=sub.currency,
                    subtotal=pro_res.prorated_amount,
                    tax_amount=0,
                    total_amount=pro_res.prorated_amount,
                    credited_amount=0,
                    paid_amount=0,
                    balance_due=pro_res.prorated_amount,
                    issue_date=eff_date,
                    due_date=eff_date,
                    billing_period_start=eff_date,
                    billing_period_end=sub.current_period_end,
                )
                inv_line = InvoiceLine(
                    sales_order_line_id=sub.sales_order_line_id,
                    subscription_id=sub.id,
                    line_type="PRORATION_CHARGE",
                    description=f"Mid-cycle subscription upgrade: {old_qty} -> {new_qty} units ({pro_res.explanation})",
                    quantity=pro_res.delta_quantity,
                    unit_price=sub.unit_price,
                    amount=pro_res.prorated_amount,
                    billing_period_start=eff_date,
                    billing_period_end=sub.current_period_end,
                )
                inv.lines.append(inv_line)
                await self.invoice_repo.create_invoice(self.db, inv)

            elif pro_res.prorated_amount < 0:
                # Quantity decrease -> issue Credit Note
                cn_amt = abs(pro_res.prorated_amount)
                cn = CreditNote(
                    credit_note_number=self._generate_cn_number(),
                    customer_id=sub.customer_id,
                    sales_order_id=sub.sales_order_id,
                    subscription_id=sub.id,
                    status="ISSUED",
                    currency=sub.currency,
                    amount=cn_amt,
                    reason=reason or f"Mid-cycle subscription quantity reduction from {old_qty} to {new_qty}",
                )
                cn_line = CreditNoteLine(
                    description=f"Prorated credit for quantity reduction: {old_qty} -> {new_qty} units",
                    quantity=abs(pro_res.delta_quantity),
                    unit_amount=sub.unit_price,
                    amount=cn_amt,
                )
                cn.lines.append(cn_line)
                await self.cn_repo.create_credit_note(self.db, cn)

            # 3. Update subscription quantity & future schedule amounts
            sub.quantity = new_qty
            for sch in sub.schedules:
                if sch.status == "SCHEDULED":
                    sch.scheduled_amount = new_qty * sub.unit_price

            if sub.sales_order_id:
                self.db.add(
                    OrderAuditEvent(
                        sales_order_id=sub.sales_order_id,
                        actor_user_id=actor_user_id,
                        event_type="SUBSCRIPTION_QUANTITY_CHANGED",
                        reason=reason,
                        event_metadata={
                            "old_quantity": float(old_qty),
                            "new_quantity": new_qty,
                            "prorated_amount": float(pro_res.prorated_amount),
                        },
                    )
                )

            await self.db.commit()
            return await self.sub_repo.get_by_id(self.db, sub.id)
        except Exception:
            await self.db.rollback()
            raise

    async def cancel_subscription(
        self,
        subscription_id: int,
        effective_date: Optional[datetime] = None,
        reason: Optional[str] = None,
        actor_user_id: Optional[int] = None,
    ) -> Subscription:
        """
        ATOMIC SUBSCRIPTION CANCELLATION:
        Handles END_OF_PERIOD vs IMMEDIATE_PRORATED_CREDIT policies.
        """
        sub = await self.sub_repo.get_by_id(self.db, subscription_id)
        if not sub:
            raise ResourceNotFoundError(f"Subscription with ID {subscription_id} not found.")

        if sub.status in {"CANCELLED", "ENDED"}:
            raise SubscriptionStateError(f"Subscription is already in '{sub.status}' state.")

        eff_date = effective_date or datetime.now(timezone.utc)

        try:
            if sub.cancellation_method == "IMMEDIATE_PRORATED_CREDIT":
                cancel_res = ProrationEngine.calculate_cancellation_credit(
                    period_start=sub.current_period_start,
                    period_end=sub.current_period_end,
                    effective_date=eff_date,
                    current_quantity=sub.quantity,
                    unit_price=sub.unit_price,
                    cancellation_method="IMMEDIATE_PRORATED_CREDIT",
                )

                if cancel_res.prorated_amount > 0:
                    cn = CreditNote(
                        credit_note_number=self._generate_cn_number(),
                        customer_id=sub.customer_id,
                        sales_order_id=sub.sales_order_id,
                        subscription_id=sub.id,
                        status="ISSUED",
                        currency=sub.currency,
                        amount=cancel_res.prorated_amount,
                        reason=reason or f"Immediate subscription cancellation credit ({cancel_res.explanation})",
                    )
                    cn_line = CreditNoteLine(
                        description=f"Prorated cancellation credit for Subscription {sub.subscription_number}",
                        quantity=sub.quantity,
                        unit_amount=sub.unit_price,
                        amount=cancel_res.prorated_amount,
                    )
                    cn.lines.append(cn_line)
                    await self.cn_repo.create_credit_note(self.db, cn)

                sub.status = "CANCELLED"
                sub.cancelled_at = eff_date
                sub.ended_at = eff_date

                # Cancel all future scheduled occurrences
                for sch in sub.schedules:
                    if sch.status == "SCHEDULED":
                        sch.status = "CANCELLED"
            else:
                # END_OF_PERIOD
                sub.status = "PENDING_CANCELLATION"
                sub.cancel_at_period_end = True
                sub.cancelled_at = eff_date

                for sch in sub.schedules:
                    if sch.billing_date > sub.current_period_end and sch.status == "SCHEDULED":
                        sch.status = "CANCELLED"

            if sub.sales_order_id:
                self.db.add(
                    OrderAuditEvent(
                        sales_order_id=sub.sales_order_id,
                        actor_user_id=actor_user_id,
                        event_type="SUBSCRIPTION_CANCELLED",
                        reason=reason,
                        event_metadata={"cancellation_method": sub.cancellation_method},
                    )
                )

            await self.db.commit()
            return await self.sub_repo.get_by_id(self.db, sub.id)
        except Exception:
            await self.db.rollback()
            raise
