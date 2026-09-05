from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order_audit_event import OrderAuditEvent
from app.models.user import User
from app.repositories.base import BaseRepository


class OrderAuditRepository(BaseRepository[OrderAuditEvent]):
    def __init__(self) -> None:
        super().__init__(OrderAuditEvent)

    def _default_options(self):
        return [
            selectinload(OrderAuditEvent.actor_user).selectinload(User.role),
        ]

    async def create_event(self, db: AsyncSession, event: OrderAuditEvent) -> OrderAuditEvent:
        db.add(event)
        await db.flush()
        return event

    async def list_events_by_order(self, db: AsyncSession, sales_order_id: int) -> List[OrderAuditEvent]:
        stmt = (
            select(OrderAuditEvent)
            .options(*self._default_options())
            .where(OrderAuditEvent.sales_order_id == sales_order_id)
            .order_by(OrderAuditEvent.created_at.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
