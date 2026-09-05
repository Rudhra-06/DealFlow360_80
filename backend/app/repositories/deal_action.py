from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.deal_action import DealAction
from app.repositories.base import BaseRepository


class DealActionRepository(BaseRepository[DealAction]):
    def __init__(self) -> None:
        super().__init__(DealAction)

    def _default_options(self):
        return [
            selectinload(DealAction.alert),
            selectinload(DealAction.quotation),
            selectinload(DealAction.target_user),
            selectinload(DealAction.created_by_user),
        ]

    async def create_action(self, db: AsyncSession, action: DealAction) -> DealAction:
        db.add(action)
        await db.flush()
        return action

    async def list_by_alert(self, db: AsyncSession, deal_alert_id: int) -> List[DealAction]:
        stmt = (
            select(DealAction)
            .options(*self._default_options())
            .where(DealAction.deal_alert_id == deal_alert_id)
            .order_by(DealAction.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
