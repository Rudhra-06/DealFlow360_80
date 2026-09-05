from datetime import datetime, timezone
import secrets
from decimal import Decimal
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order_audit_event import OrderAuditEvent
from app.models.payment import Payment
from app.models.payment_allocation import PaymentAllocation
from app.repositories.invoice import InvoiceRepository
from app.repositories.payment import PaymentRepository
from app.repositories.sales_order import SalesOrderRepository
from app.services.exceptions import (
    CurrencyMismatchError,
    InvalidPaymentAllocationError,
    OverpaymentError,
    ResourceNotFoundError,
)
from app.services.notification import NotificationService


class PaymentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.payment_repo = PaymentRepository()
        self.invoice_repo = InvoiceRepository()
        self.order_repo = SalesOrderRepository()
        self.notif_service = NotificationService(db)

    def _generate_payment_number(self) -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        rand_suffix = secrets.token_hex(4).upper()
        return f"PAY-{date_str}-{rand_suffix}"

    async def record_payment(
        self,
        customer_id: int,
        amount: float,
        currency: str,
        payment_method: str,
        allocations_input: List[Dict[str, any]],
        recorded_by_user_id: int,
        reference: Optional[str] = None,
    ) -> Payment:
        """
        ATOMIC PAYMENT TRANSACTION:
        1. Validates total allocation amount matches payment amount.
        2. Validates customer and currency match across all allocated invoices.
        3. Validates allocation does NOT exceed invoice balance_due (prevents overpayment).
        4. Updates paid_amount, balance_due, and status (ISSUED -> PARTIALLY_PAID -> PAID).
        5. Updates parent SalesOrder status.
        6. Logs audit and dispatches real-time events post-commit.
        """
        pay_amt = Decimal(str(amount))
        if pay_amt <= Decimal("0.00"):
            raise InvalidPaymentAllocationError("Payment amount must be greater than zero.")

        total_allocated = sum((Decimal(str(item["amount"])) for item in allocations_input), Decimal("0.00"))
        if total_allocated != pay_amt:
            raise InvalidPaymentAllocationError(
                f"Sum of allocations ({total_allocated}) does not match payment amount ({pay_amt})."
            )

        # Domain Validation Phase (No ORM mutations, no try-except rollback wrapper)
        validated_items = []
        for item in allocations_input:
            inv_id = item["invoice_id"]
            alloc_amt = Decimal(str(item["amount"]))

            if alloc_amt <= Decimal("0.00"):
                raise InvalidPaymentAllocationError(f"Allocation amount for invoice {inv_id} must be > 0.")

            inv = await self.invoice_repo.get_by_id(self.db, inv_id)
            if not inv:
                raise ResourceNotFoundError(f"Invoice with ID {inv_id} not found.")

            if inv.customer_id != customer_id:
                raise InvalidPaymentAllocationError(f"Invoice {inv_id} does not belong to customer {customer_id}.")

            if inv.currency.upper() != currency.upper():
                raise CurrencyMismatchError(f"Payment currency ({currency}) does not match invoice currency ({inv.currency}).")

            if alloc_amt > inv.balance_due:
                raise OverpaymentError(
                    f"Allocation amount {alloc_amt} exceeds balance due {inv.balance_due} for invoice {inv.invoice_number}."
                )

            validated_items.append((inv, alloc_amt))

        # Mutation & Persistence Phase
        try:
            now = datetime.now(timezone.utc)
            payment = Payment(
                payment_number=self._generate_payment_number(),
                customer_id=customer_id,
                currency=currency.upper(),
                amount=pay_amt,
                payment_method=payment_method,
                reference=reference,
                received_at=now,
                recorded_by_user_id=recorded_by_user_id,
                status="RECORDED",
            )

            affected_orders = set()

            for inv, alloc_amt in validated_items:
                # Update invoice financial state
                inv.paid_amount += alloc_amt
                inv.balance_due = max(Decimal("0.00"), inv.total_amount - inv.credited_amount - inv.paid_amount)

                if inv.balance_due == Decimal("0.00"):
                    inv.status = "PAID"
                    inv.paid_at = now
                else:
                    inv.status = "PARTIALLY_PAID"

                alloc_obj = PaymentAllocation(
                    invoice_id=inv.id,
                    amount=alloc_amt,
                )
                payment.allocations.append(alloc_obj)
                affected_orders.add(inv.sales_order_id)

            await self.payment_repo.create_payment(self.db, payment)

            # Update status for affected orders
            for order_id in affected_orders:
                order = await self.order_repo.get_by_id(self.db, order_id)
                if order:
                    order_invoices = await self.invoice_repo.list_by_order(self.db, order_id)
                    all_paid = all(inv.status in {"PAID", "CREDITED"} for inv in order_invoices)
                    any_paid = any(inv.status in {"PAID", "PARTIALLY_PAID", "CREDITED"} for inv in order_invoices)

                    if all_paid:
                        if order.status != "ACTIVE_SUBSCRIPTION":
                            order.status = "PAID"
                    elif any_paid:
                        if order.status != "ACTIVE_SUBSCRIPTION":
                            order.status = "PARTIALLY_PAID"

                    self.db.add(
                        OrderAuditEvent(
                            sales_order_id=order.id,
                            actor_user_id=recorded_by_user_id,
                            event_type="PAYMENT_RECORDED",
                            to_status=order.status,
                            event_metadata={
                                "payment_number": payment.payment_number,
                                "amount": float(pay_amt),
                            },
                        )
                    )

            await self.db.commit()

            # Post-commit notification dispatch
            for order_id in affected_orders:
                order = await self.order_repo.get_by_id(self.db, order_id)
                if order:
                    await self.notif_service.dispatch_post_commit_events(
                        target_user_ids=[order.sales_rep_id],
                        event_name="payment.received",
                        quotation_id=order.quotation_id,
                        payload={"payment_number": payment.payment_number, "amount": float(pay_amt)},
                        title=f"Payment Received: {payment.payment_number}",
                        message_text=f"Payment of {currency} {pay_amt} recorded for Order {order.order_number}.",
                    )

            return await self.payment_repo.get_by_id(self.db, payment.id)
        except Exception:
            await self.db.rollback()
            raise

    async def get_payment(self, payment_id: int) -> Payment:
        pay = await self.payment_repo.get_by_id(self.db, payment_id)
        if not pay:
            raise ResourceNotFoundError(f"Payment with ID {payment_id} not found.")
        return pay

    async def list_payments(
        self,
        customer_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Payment]:
        return await self.payment_repo.list_payments(
            self.db, customer_id=customer_id, status=status, limit=limit, offset=offset
        )
