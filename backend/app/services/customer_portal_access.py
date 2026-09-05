from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.roles import RoleName
from app.models.customer_portal_access import CustomerPortalAccess
from app.repositories.customer import CustomerRepository
from app.repositories.customer_portal_access import CustomerPortalAccessRepository
from app.repositories.user import UserRepository
from app.schemas.customer_portal_access import CustomerPortalAccessCreate, CustomerPortalAccessUpdate
from app.services.exceptions import (
    CommercialPolicyValidationError,
    InactiveReferenceError,
    InvalidReferenceError,
    QuoteAccessDeniedError,
    ResourceNotFoundError,
)


class CustomerPortalAccessService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.access_repo = CustomerPortalAccessRepository()
        self.user_repo = UserRepository()
        self.customer_repo = CustomerRepository()

    async def create_access(self, obj_in: CustomerPortalAccessCreate) -> CustomerPortalAccess:
        # 1. Validate User exists & role is CUSTOMER
        user = await self.user_repo.get_by_id(self.db, obj_in.user_id)
        if not user:
            raise InvalidReferenceError(f"User with ID {obj_in.user_id} does not exist.")
        if not user.role or user.role.name != RoleName.CUSTOMER:
            raise CommercialPolicyValidationError(f"User '{user.email}' does not have the CUSTOMER role.")

        # 2. Validate Customer exists & is active
        customer = await self.customer_repo.get_by_id(self.db, obj_in.customer_id)
        if not customer:
            raise InvalidReferenceError(f"Customer with ID {obj_in.customer_id} does not exist.")
        if not customer.is_active:
            raise InactiveReferenceError(f"Customer '{customer.name}' is inactive.")

        # 3. Check for existing mapping
        existing = await self.access_repo.get_by_user_id(self.db, obj_in.user_id)
        if existing and existing.is_active:
            raise CommercialPolicyValidationError(f"User with ID {obj_in.user_id} already has an active Customer portal mapping.")

        try:
            if existing:
                existing.customer_id = customer.id
                existing.is_active = obj_in.is_active
                await self.db.flush()
                await self.db.commit()
                return await self.access_repo.get_by_id(self.db, existing.id)

            access = CustomerPortalAccess(
                user_id=user.id,
                customer_id=customer.id,
                is_active=obj_in.is_active,
            )
            await self.access_repo.create_access(self.db, access)
            await self.db.commit()
            return await self.access_repo.get_by_id(self.db, access.id)
        except Exception:
            await self.db.rollback()
            raise

    async def update_access(self, access_id: int, obj_in: CustomerPortalAccessUpdate) -> CustomerPortalAccess:
        access = await self.access_repo.get_by_id(self.db, access_id)
        if not access:
            raise ResourceNotFoundError(f"CustomerPortalAccess with ID {access_id} not found.")

        try:
            if obj_in.is_active is not None:
                access.is_active = obj_in.is_active
            await self.db.flush()
            await self.db.commit()
            return await self.access_repo.get_by_id(self.db, access_id)
        except Exception:
            await self.db.rollback()
            raise

    async def list_access(
        self,
        customer_id: Optional[int] = None,
        user_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CustomerPortalAccess]:
        return await self.access_repo.list_access(
            self.db, customer_id=customer_id, user_id=user_id, is_active=is_active, limit=limit, offset=offset
        )

    async def get_active_customer_id_for_user(self, user_id: int) -> int:
        access = await self.access_repo.get_active_by_user_id(self.db, user_id)
        if not access or not access.customer or not access.customer.is_active:
            raise QuoteAccessDeniedError("Customer portal user does not have an active customer account association.")
        return access.customer_id
