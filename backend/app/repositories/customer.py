from typing import List, Optional
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    def __init__(self) -> None:
        super().__init__(Customer)

    async def get_by_code(self, db: AsyncSession, customer_code: str) -> Optional[Customer]:
        result = await db.execute(
            select(Customer)
            .options(selectinload(Customer.tier))
            .where(Customer.customer_code == customer_code)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[Customer]:
        result = await db.execute(
            select(Customer)
            .options(selectinload(Customer.tier))
            .where(Customer.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_tier(self, db: AsyncSession, customer_id: int) -> Optional[Customer]:
        result = await db.execute(
            select(Customer)
            .options(selectinload(Customer.tier))
            .where(Customer.id == customer_id)
        )
        return result.scalar_one_or_none()

    async def list_customers(
        self,
        db: AsyncSession,
        tier_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Customer]:
        stmt = select(Customer).options(selectinload(Customer.tier))

        if tier_id is not None:
            stmt = stmt.where(Customer.tier_id == tier_id)
        if is_active is not None:
            stmt = stmt.where(Customer.is_active == is_active)
        if search:
            search_pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Customer.customer_code.ilike(search_pattern),
                    Customer.name.ilike(search_pattern),
                    Customer.email.ilike(search_pattern),
                )
            )

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())
