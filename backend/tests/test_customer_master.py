import uuid
from decimal import Decimal
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.schemas.customer_tier import CustomerTierCreate, CustomerTierUpdate
from app.services.customer import CustomerService
from app.services.customer_tier import CustomerTierService
from app.services.exceptions import (
    DuplicateResourceError,
    InactiveReferenceError,
    InvalidReferenceError,
    ResourceNotFoundError,
)


@pytest.mark.anyio
async def test_customer_tier_service_crud(db_session: AsyncSession):
    service = CustomerTierService(db_session)
    name = f"TIER_{uuid.uuid4().hex[:6]}"

    # Create
    tier = await service.create_tier(CustomerTierCreate(name=name, description="Test Tier"))
    assert tier.id is not None
    assert tier.name == name
    assert tier.is_active is True

    # Get
    fetched = await service.get_tier_by_id(tier.id)
    assert fetched.name == name

    # Update
    updated = await service.update_tier(tier.id, CustomerTierUpdate(description="Updated Desc"))
    assert updated.description == "Updated Desc"

    # Duplicate create raises 409
    with pytest.raises(DuplicateResourceError):
        await service.create_tier(CustomerTierCreate(name=name))


@pytest.mark.anyio
async def test_customer_service_crud_and_normalization(db_session: AsyncSession):
    tier_service = CustomerTierService(db_session)
    tier = await tier_service.create_tier(
        CustomerTierCreate(name=f"TIER_CUST_{uuid.uuid4().hex[:6]}")
    )

    cust_service = CustomerService(db_session)
    uid = uuid.uuid4().hex[:6]

    # Create with un-normalized code and email
    cust_in = CustomerCreate(
        customer_code=f"  cust-{uid}  ",
        name="  Acme Test Corp  ",
        email=f"  TEST-{uid}@EXAMPLE.COM  ",
        tier_id=tier.id,
        credit_limit=Decimal("15000.50"),
        currency="usd",
    )
    cust = await cust_service.create_customer(cust_in)
    assert cust.id is not None
    assert cust.customer_code == f"CUST-{uid.upper()}"
    assert cust.name == "Acme Test Corp"
    assert cust.email == f"test-{uid}@example.com"
    assert cust.currency == "USD"
    assert cust.credit_limit == Decimal("15000.50")
    assert cust.tier.id == tier.id

    # Duplicate code raises DuplicateResourceError
    with pytest.raises(DuplicateResourceError):
        await cust_service.create_customer(
            CustomerCreate(
                customer_code=f"cust-{uid}",
                name="Duplicate Code Corp",
                tier_id=tier.id,
            )
        )

    # Duplicate email raises DuplicateResourceError
    with pytest.raises(DuplicateResourceError):
        await cust_service.create_customer(
            CustomerCreate(
                customer_code=f"CUST-NEW-{uid}",
                name="Duplicate Email Corp",
                email=f"test-{uid}@example.com",
                tier_id=tier.id,
            )
        )


@pytest.mark.anyio
async def test_customer_inactive_tier_validation(db_session: AsyncSession):
    tier_service = CustomerTierService(db_session)
    tier = await tier_service.create_tier(
        CustomerTierCreate(name=f"INACT_TIER_{uuid.uuid4().hex[:6]}", is_active=False)
    )

    cust_service = CustomerService(db_session)

    # Attempting to assign customer to inactive tier fails
    with pytest.raises(InactiveReferenceError):
        await cust_service.create_customer(
            CustomerCreate(
                customer_code=f"CUST-INACT-{uuid.uuid4().hex[:6]}",
                name="Inactive Tier Customer",
                tier_id=tier.id,
            )
        )


@pytest.mark.anyio
async def test_customer_nonexistent_tier_validation(db_session: AsyncSession):
    cust_service = CustomerService(db_session)

    # Nonexistent tier ID raises InvalidReferenceError
    with pytest.raises(InvalidReferenceError):
        await cust_service.create_customer(
            CustomerCreate(
                customer_code=f"CUST-NONEXIST-{uuid.uuid4().hex[:6]}",
                name="Nonexistent Tier Customer",
                tier_id=999999,
            )
        )
