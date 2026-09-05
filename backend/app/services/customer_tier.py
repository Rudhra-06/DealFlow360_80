from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer_tier import CustomerTier
from app.repositories.customer_tier import CustomerTierRepository
from app.schemas.customer_tier import CustomerTierCreate, CustomerTierUpdate
from app.services.exceptions import DuplicateResourceError, ResourceNotFoundError


class CustomerTierService:
    def __init__(self, db: AsyncSession) -> None:
        self.db: AsyncSession = db
        self.repo: CustomerTierRepository = CustomerTierRepository()

    async def get_tier_by_id(self, tier_id: int) -> CustomerTier:
        tier = await self.repo.get_by_id(self.db, tier_id)
        if not tier:
            raise ResourceNotFoundError(f"CustomerTier with ID {tier_id} not found.")
        return tier

    async def list_tiers(
        self, is_active: Optional[bool] = None, limit: int = 100, offset: int = 0
    ) -> List[CustomerTier]:
        return await self.repo.list_tiers(
            self.db, is_active=is_active, limit=limit, offset=offset
        )

    async def create_tier(self, data: CustomerTierCreate) -> CustomerTier:
        name_clean = data.name.strip()
        existing = await self.repo.get_by_name(self.db, name_clean)
        if existing:
            raise DuplicateResourceError(f"CustomerTier with name '{name_clean}' already exists.")

        tier = CustomerTier(
            name=name_clean,
            description=data.description.strip() if data.description else None,
            is_active=data.is_active,
        )
        await self.repo.add(self.db, tier)

        try:
            await self.db.commit()
            await self.db.refresh(tier)
            return tier
        except Exception:
            await self.db.rollback()
            raise

    async def update_tier(self, tier_id: int, data: CustomerTierUpdate) -> CustomerTier:
        tier = await self.get_tier_by_id(tier_id)
        update_dict = data.model_dump(exclude_unset=True)

        if "name" in update_dict and update_dict["name"] is not None:
            name_clean = update_dict["name"].strip()
            if name_clean != tier.name:
                existing = await self.repo.get_by_name(self.db, name_clean)
                if existing:
                    raise DuplicateResourceError(
                        f"CustomerTier with name '{name_clean}' already exists."
                    )
                tier.name = name_clean

        if "description" in update_dict:
            tier.description = (
                update_dict["description"].strip() if update_dict["description"] else None
            )
        if "is_active" in update_dict and update_dict["is_active"] is not None:
            tier.is_active = update_dict["is_active"]

        try:
            await self.db.commit()
            await self.db.refresh(tier)
            return tier
        except Exception:
            await self.db.rollback()
            raise
