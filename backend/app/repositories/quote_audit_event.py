from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quote_audit_event import QuoteAuditEvent
from app.repositories.base import BaseRepository


class QuoteAuditEventRepository(BaseRepository[QuoteAuditEvent]):
    def __init__(self) -> None:
        super().__init__(QuoteAuditEvent)

    async def create_event(self, db: AsyncSession, event: QuoteAuditEvent) -> QuoteAuditEvent:
        db.add(event)
        await db.flush()
        return event

    async def list_by_quotation(
        self, db: AsyncSession, quotation_id: int
    ) -> List[QuoteAuditEvent]:
        stmt = (
            select(QuoteAuditEvent)
            .options(selectinload(QuoteAuditEvent.actor_user))
            .where(QuoteAuditEvent.quotation_id == quotation_id)
            .order_by(QuoteAuditEvent.created_at.asc(), QuoteAuditEvent.id.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
