from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.repositories.customer import CustomerRepository
from app.repositories.customer_tier import CustomerTierRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.services.exceptions import (
    DuplicateResourceError,
    InactiveReferenceError,
    InvalidReferenceError,
    ResourceNotFoundError,
)


class CustomerService:
    def __init__(self, db: AsyncSession) -> None:
        self.db: AsyncSession = db
        self.customer_repo: CustomerRepository = CustomerRepository()
        self.tier_repo: CustomerTierRepository = CustomerTierRepository()

    async def get_customer_by_id(self, customer_id: int) -> Customer:
        customer = await self.customer_repo.get_by_id_with_tier(self.db, customer_id)
        if not customer:
            raise ResourceNotFoundError(f"Customer with ID {customer_id} not found.")
        return customer

    async def list_customers(
        self,
        tier_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Customer]:
        return await self.customer_repo.list_customers(
            self.db,
            tier_id=tier_id,
            is_active=is_active,
            search=search,
            limit=limit,
            offset=offset,
        )

    async def create_customer(self, data: CustomerCreate) -> Customer:
        # 1. Customer Code Normalization
        code_clean = data.customer_code.strip().upper()
        existing_code = await self.customer_repo.get_by_code(self.db, code_clean)
        if existing_code:
            raise DuplicateResourceError(f"Customer with code '{code_clean}' already exists.")

        # 2. Email Normalization & Duplicate Check (if provided)
        email_clean: Optional[str] = None
        if data.email:
            email_clean = str(data.email).strip().lower()
            existing_email = await self.customer_repo.get_by_email(self.db, email_clean)
            if existing_email:
                raise DuplicateResourceError(f"Customer with email '{email_clean}' already exists.")

        # 3. Tier Validation
        tier = await self.tier_repo.get_by_id(self.db, data.tier_id)
        if not tier:
            raise InvalidReferenceError(f"CustomerTier with ID {data.tier_id} does not exist.")
        if not tier.is_active:
            raise InactiveReferenceError(f"Cannot assign customer to inactive CustomerTier '{tier.name}'.")

        # 4. Currency Normalization
        currency_clean = data.currency.strip().upper()

        customer = Customer(
            customer_code=code_clean,
            name=data.name.strip(),
            email=email_clean,
            phone=data.phone.strip() if data.phone else None,
            tier_id=data.tier_id,
            billing_address=data.billing_address.strip() if data.billing_address else None,
            shipping_address=data.shipping_address.strip() if data.shipping_address else None,
            default_payment_terms_days=data.default_payment_terms_days,
            credit_limit=data.credit_limit,
            currency=currency_clean,
            is_active=data.is_active,
        )

        await self.customer_repo.add(self.db, customer)

        try:
            await self.db.commit()
            return await self.get_customer_by_id(customer.id)
        except Exception:
            await self.db.rollback()
            raise

    async def update_customer(self, customer_id: int, data: CustomerUpdate) -> Customer:
        customer = await self.get_customer_by_id(customer_id)
        update_dict = data.model_dump(exclude_unset=True)

        if "customer_code" in update_dict and update_dict["customer_code"] is not None:
            code_clean = update_dict["customer_code"].strip().upper()
            if code_clean != customer.customer_code:
                existing = await self.customer_repo.get_by_code(self.db, code_clean)
                if existing:
                    raise DuplicateResourceError(f"Customer with code '{code_clean}' already exists.")
                customer.customer_code = code_clean

        if "email" in update_dict:
            if update_dict["email"] is None:
                customer.email = None
            else:
                email_clean = str(update_dict["email"]).strip().lower()
                if email_clean != customer.email:
                    existing = await self.customer_repo.get_by_email(self.db, email_clean)
                    if existing:
                        raise DuplicateResourceError(f"Customer with email '{email_clean}' already exists.")
                    customer.email = email_clean

        if "tier_id" in update_dict and update_dict["tier_id"] is not None:
            tier_id = update_dict["tier_id"]
            if tier_id != customer.tier_id:
                tier = await self.tier_repo.get_by_id(self.db, tier_id)
                if not tier:
                    raise InvalidReferenceError(f"CustomerTier with ID {tier_id} does not exist.")
                if not tier.is_active:
                    raise InactiveReferenceError(f"Cannot assign customer to inactive CustomerTier '{tier.name}'.")
                customer.tier_id = tier_id

        if "name" in update_dict and update_dict["name"] is not None:
            customer.name = update_dict["name"].strip()
        if "phone" in update_dict:
            customer.phone = update_dict["phone"].strip() if update_dict["phone"] else None
        if "billing_address" in update_dict:
            customer.billing_address = update_dict["billing_address"].strip() if update_dict["billing_address"] else None
        if "shipping_address" in update_dict:
            customer.shipping_address = update_dict["shipping_address"].strip() if update_dict["shipping_address"] else None
        if "default_payment_terms_days" in update_dict and update_dict["default_payment_terms_days"] is not None:
            customer.default_payment_terms_days = update_dict["default_payment_terms_days"]
        if "credit_limit" in update_dict and update_dict["credit_limit"] is not None:
            customer.credit_limit = update_dict["credit_limit"]
        if "currency" in update_dict and update_dict["currency"] is not None:
            customer.currency = update_dict["currency"].strip().upper()
        if "is_active" in update_dict and update_dict["is_active"] is not None:
            customer.is_active = update_dict["is_active"]

        try:
            await self.db.commit()
            return await self.get_customer_by_id(customer.id)
        except Exception:
            await self.db.rollback()
            raise
