from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product_recommendation_rule import ProductRecommendationRule
from app.repositories.base import BaseRepository


class ProductRecommendationRuleRepository(BaseRepository[ProductRecommendationRule]):
    def __init__(self) -> None:
        super().__init__(ProductRecommendationRule)

    def _default_options(self):
        return [
            selectinload(ProductRecommendationRule.source_product),
            selectinload(ProductRecommendationRule.suggested_product),
        ]

    async def create_rule(
        self, db: AsyncSession, rule: ProductRecommendationRule
    ) -> ProductRecommendationRule:
        db.add(rule)
        await db.flush()
        return rule

    async def get_by_id(self, db: AsyncSession, rule_id: int) -> Optional[ProductRecommendationRule]:
        stmt = (
            select(ProductRecommendationRule)
            .options(*self._default_options())
            .where(ProductRecommendationRule.id == rule_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_rules(
        self,
        db: AsyncSession,
        source_product_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        is_promoted: Optional[bool] = None,
        effective_only: bool = False,
        as_of: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ProductRecommendationRule]:
        stmt = select(ProductRecommendationRule).options(*self._default_options())
        filters = []

        if source_product_id is not None:
            filters.append(ProductRecommendationRule.source_product_id == source_product_id)
        if is_active is not None:
            filters.append(ProductRecommendationRule.is_active == is_active)
        if is_promoted is not None:
            filters.append(ProductRecommendationRule.is_promoted == is_promoted)

        if effective_only:
            now = as_of or datetime.now(timezone.utc)
            filters.append(ProductRecommendationRule.is_active == True)
            filters.append(ProductRecommendationRule.effective_from <= now)
            filters.append(
                or_(
                    ProductRecommendationRule.effective_to == None,
                    ProductRecommendationRule.effective_to > now,
                )
            )

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = (
            stmt.order_by(
                ProductRecommendationRule.is_promoted.desc(),
                ProductRecommendationRule.affinity_score.desc(),
                ProductRecommendationRule.priority.asc(),
            )
            .offset(offset)
            .limit(limit)
        )

        result = await db.execute(stmt)
        return list(result.scalars().all())
