from datetime import datetime, timezone
from typing import Optional, Sequence
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval_policy import ApprovalPolicy
from app.repositories.base import BaseRepository
from app.schemas.approval_policy import ApprovalPolicyCreate


class ApprovalPolicyRepository(BaseRepository[ApprovalPolicy]):
    def __init__(self):
        super().__init__(ApprovalPolicy)

    async def create_policy(
        self, db: AsyncSession, obj_in: ApprovalPolicyCreate
    ) -> ApprovalPolicy:
        policy = ApprovalPolicy(**obj_in.model_dump())
        db.add(policy)
        await db.flush()
        return policy

    async def get_by_id(self, db: AsyncSession, policy_id: int) -> Optional[ApprovalPolicy]:
        stmt = select(ApprovalPolicy).where(ApprovalPolicy.id == policy_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_policies(
        self,
        db: AsyncSession,
        customer_tier_id: Optional[int] = None,
        approval_role: Optional[str] = None,
        is_active: Optional[bool] = None,
        effective_only: bool = False,
        as_of: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ApprovalPolicy]:
        stmt = select(ApprovalPolicy)
        filters = []

        if customer_tier_id is not None:
            filters.append(ApprovalPolicy.customer_tier_id == customer_tier_id)
        if approval_role is not None:
            filters.append(ApprovalPolicy.approval_role == approval_role)
        if is_active is not None:
            filters.append(ApprovalPolicy.is_active == is_active)

        if effective_only:
            now = as_of or datetime.now(timezone.utc)
            filters.append(ApprovalPolicy.is_active == True)
            filters.append(
                or_(
                    ApprovalPolicy.effective_from == None,
                    ApprovalPolicy.effective_from <= now,
                )
            )
            filters.append(
                or_(
                    ApprovalPolicy.effective_to == None,
                    ApprovalPolicy.effective_to > now,
                )
            )

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(ApprovalPolicy.priority.asc(), ApprovalPolicy.id.asc()).offset(offset).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
