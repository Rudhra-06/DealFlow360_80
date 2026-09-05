from typing import List, Set
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quote_recommendation_dismissal import QuoteRecommendationDismissal
from app.repositories.base import BaseRepository


class QuoteRecommendationDismissalRepository(BaseRepository[QuoteRecommendationDismissal]):
    def __init__(self) -> None:
        super().__init__(QuoteRecommendationDismissal)

    async def add_dismissal(
        self, db: AsyncSession, dismissal: QuoteRecommendationDismissal
    ) -> QuoteRecommendationDismissal:
        db.add(dismissal)
        await db.flush()
        return dismissal

    async def get_dismissed_rule_ids(self, db: AsyncSession, quotation_id: int) -> Set[int]:
        stmt = select(QuoteRecommendationDismissal.recommendation_rule_id).where(
            QuoteRecommendationDismissal.quotation_id == quotation_id
        )
        result = await db.execute(stmt)
        return set(result.scalars().all())
