from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credit_note import CreditNote
from app.models.order_audit_event import OrderAuditEvent
from app.repositories.credit_note import CreditNoteRepository
from app.repositories.invoice import InvoiceRepository
from app.services.exceptions import (
    CreditApplicationError,
    CurrencyMismatchError,
    ResourceNotFoundError,
)


class CreditNoteService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.cn_repo = CreditNoteRepository()
        self.invoice_repo = InvoiceRepository()

    async def apply_credit_note_to_invoice(
        self, credit_note_id: int, invoice_id: int, actor_user_id: Optional[int] = None
    ) -> CreditNote:
        """
        ATOMIC CREDIT APPLICATION:
        Applies an ISSUED credit note to reduce balance_due on an open invoice for the same customer & currency.
        """
        cn = await self.cn_repo.get_by_id(self.db, credit_note_id)
        if not cn:
            raise ResourceNotFoundError(f"CreditNote with ID {credit_note_id} not found.")

        if cn.status != "ISSUED":
            raise CreditApplicationError(f"CreditNote {credit_note_id} is in '{cn.status}' status and cannot be applied.")

        inv = await self.invoice_repo.get_by_id(self.db, invoice_id)
        if not inv:
            raise ResourceNotFoundError(f"Invoice with ID {invoice_id} not found.")

        if inv.customer_id != cn.customer_id:
            raise CreditApplicationError("CreditNote and target Invoice must belong to the same customer.")

        if inv.currency != cn.currency:
            raise CurrencyMismatchError(f"CreditNote currency ({cn.currency}) does not match invoice currency ({inv.currency}).")

        if inv.balance_due <= Decimal("0.00"):
            raise CreditApplicationError(f"Invoice {invoice_id} has zero balance due and cannot receive credit.")

        try:
            applied_amt = min(cn.amount, inv.balance_due)

            inv.credited_amount += applied_amt
            inv.balance_due = max(Decimal("0.00"), inv.total_amount - inv.credited_amount - inv.paid_amount)

            if inv.balance_due == Decimal("0.00"):
                if inv.paid_amount == Decimal("0.00"):
                    inv.status = "CREDITED"
                else:
                    inv.status = "PAID"

            cn.status = "APPLIED"
            cn.invoice_id = inv.id
            cn.applied_at = datetime.now(timezone.utc)

            self.db.add(
                OrderAuditEvent(
                    sales_order_id=inv.sales_order_id,
                    actor_user_id=actor_user_id,
                    event_type="CREDIT_NOTE_CREATED",
                    event_metadata={
                        "credit_note_number": cn.credit_note_number,
                        "applied_amount": float(applied_amt),
                        "invoice_id": inv.id,
                    },
                )
            )

            await self.db.commit()
            return await self.cn_repo.get_by_id(self.db, cn.id)
        except Exception:
            await self.db.rollback()
            raise

    async def get_credit_note(self, credit_note_id: int) -> CreditNote:
        cn = await self.cn_repo.get_by_id(self.db, credit_note_id)
        if not cn:
            raise ResourceNotFoundError(f"CreditNote with ID {credit_note_id} not found.")
        return cn

    async def list_credit_notes(
        self,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        sales_order_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CreditNote]:
        return await self.cn_repo.list_credit_notes(
            self.db, status=status, customer_id=customer_id, sales_order_id=sales_order_id, limit=limit, offset=offset
        )
