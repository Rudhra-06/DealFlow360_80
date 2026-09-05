from datetime import datetime, timezone
from typing import Optional, Sequence
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discount_policy import DiscountPolicy
from app.repositories.base import BaseRepository
from app.schemas.discount_policy import DiscountPolicyCreate


class DiscountPolicyRepository(BaseRepository[DiscountPolicy]):
    def __init__(self):
        super().__init__(DiscountPolicy)

    async def create_policy(
        self, db: AsyncSession, obj_in: DiscountPolicyCreate
    ) -> DiscountPolicy:
        policy = DiscountPolicy(**obj_in.model_dump())
        db.add(policy)
        await db.flush()
        return policy

    async def get_by_id(self, db: AsyncSession, policy_id: int) -> Optional[DiscountPolicy]:
        stmt = select(DiscountPolicy).where(DiscountPolicy.id == policy_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_policies(
        self,
        db: AsyncSession,
        customer_tier_id: Optional[int] = None,
        product_category_id: Optional[int] = None,
        product_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        effective_only: bool = False,
        as_of: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[DiscountPolicy]:
        stmt = select(DiscountPolicy)
        filters = []

        if customer_tier_id is not None:
            filters.append(DiscountPolicy.customer_tier_id == customer_tier_id)
        if product_category_id is not None:
            filters.append(DiscountPolicy.product_category_id == product_category_id)
        if product_id is not None:
            filters.append(DiscountPolicy.product_id == product_id)
        if is_active is not None:
            filters.append(DiscountPolicy.is_active == is_active)

        if effective_only:
            now = as_of or datetime.now(timezone.utc)
            filters.append(DiscountPolicy.is_active == True)
            filters.append(DiscountPolicy.effective_from <= now)
            filters.append(
                or_(
                    DiscountPolicy.effective_to == None,
                    DiscountPolicy.effective_to > now,
                )
            )

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(DiscountPolicy.priority.asc(), DiscountPolicy.id.asc()).offset(offset).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def find_effective_candidates(
        self,
        db: AsyncSession,
        customer_tier_id: Optional[int],
        product_category_id: Optional[int],
        product_id: Optional[int],
        as_of: datetime,
    ) -> Sequence[DiscountPolicy]:
        """Queries effective policies that match tier/category/product scopes or global scope."""
        tier_condition = (DiscountPolicy.customer_tier_id == customer_tier_id) if customer_tier_id else (DiscountPolicy.customer_tier_id == None)
        tier_filter = or_(DiscountPolicy.customer_tier_id == None, DiscountPolicy.customer_tier_id == customer_tier_id) if customer_tier_id else (DiscountPolicy.customer_tier_id == None)

        product_filter = (DiscountPolicy.product_id == None)
        if product_id is not None:
            product_filter = or_(DiscountPolicy.product_id == None, DiscountPolicy.product_id == product_id)

        category_filter = (DiscountPolicy.product_category_id == None)
        if product_category_id is not None:
            category_filter = or_(DiscountPolicy.product_category_id == None, DiscountPolicy.product_category_id == product_category_id)

        stmt = select(DiscountPolicy).where(
            and_(
                DiscountPolicy.is_active == True,
                DiscountPolicy.effective_from <= as_of,
                or_(
                    DiscountPolicy.effective_to == None,
                    DiscountPolicy.effective_to > as_of,
                ),
                tier_filter,
                product_filter,
                category_filter,
            )
        ).order_by(DiscountPolicy.priority.asc(), DiscountPolicy.id.asc())

        result = await db.execute(stmt)
        return result.scalars().all()

    async def find_scope_overlaps(
        self,
        db: AsyncSession,
        customer_tier_id: Optional[int],
        product_category_id: Optional[int],
        product_id: Optional[int],
        priority: int,
        effective_from: datetime,
        effective_to: Optional[datetime],
        exclude_policy_id: Optional[int] = None,
    ) -> Sequence[DiscountPolicy]:
        """Finds active policies with exact identical scope and priority that overlap in effective time range."""
        filters = [
            DiscountPolicy.is_active == True,
            DiscountPolicy.customer_tier_id == customer_tier_id,
            DiscountPolicy.product_category_id == product_category_id,
            DiscountPolicy.product_id == product_id,
            DiscountPolicy.priority == priority,
        ]

        if exclude_policy_id is not None:
            filters.append(DiscountPolicy.id != exclude_policy_id)

        # Date overlap check: (StartA < EndB) AND (EndA > StartB)
        if effective_to is not None:
            filters.append(
                and_(
                    DiscountPolicy.effective_from < effective_to,
                    or_(
                        DiscountPolicy.effective_to == None,
                        DiscountPolicy.effective_to > effective_from,
                    ),
                )
            )
        else:
            filters.append(
                or_(
                    DiscountPolicy.effective_to == None,
                    DiscountPolicy.effective_to > effective_from,
                )
            )

        stmt = select(DiscountPolicy).where(and_(*filters))
        result = await db.execute(stmt)
        return result.scalars().all()
