from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.models.customer_portal_access import CustomerPortalAccess
from app.models.user import User
from app.repositories.base import BaseRepository


class CustomerPortalAccessRepository(BaseRepository[CustomerPortalAccess]):
    def __init__(self) -> None:
        super().__init__(CustomerPortalAccess)

    def _default_options(self):
        return [
            selectinload(CustomerPortalAccess.user).selectinload(User.role),
            selectinload(CustomerPortalAccess.customer).selectinload(Customer.tier),
        ]

    async def create_access(self, db: AsyncSession, access: CustomerPortalAccess) -> CustomerPortalAccess:
        db.add(access)
        await db.flush()
        return access

    async def get_by_id(self, db: AsyncSession, access_id: int) -> Optional[CustomerPortalAccess]:
        stmt = select(CustomerPortalAccess).options(*self._default_options()).where(CustomerPortalAccess.id == access_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_user_id(self, db: AsyncSession, user_id: int) -> Optional[CustomerPortalAccess]:
        stmt = select(CustomerPortalAccess).options(*self._default_options()).where(CustomerPortalAccess.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_active_by_user_id(self, db: AsyncSession, user_id: int) -> Optional[CustomerPortalAccess]:
        stmt = (
            select(CustomerPortalAccess)
            .options(*self._default_options())
            .where(CustomerPortalAccess.user_id == user_id, CustomerPortalAccess.is_active == True)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_access(
        self,
        db: AsyncSession,
        customer_id: Optional[int] = None,
        user_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CustomerPortalAccess]:
        stmt = select(CustomerPortalAccess).options(*self._default_options())
        if customer_id is not None:
            stmt = stmt.where(CustomerPortalAccess.customer_id == customer_id)
        if user_id is not None:
            stmt = stmt.where(CustomerPortalAccess.user_id == user_id)
        if is_active is not None:
            stmt = stmt.where(CustomerPortalAccess.is_active == is_active)

        stmt = stmt.order_by(CustomerPortalAccess.id.desc()).offset(offset).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())
