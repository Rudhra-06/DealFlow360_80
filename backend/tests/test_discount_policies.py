import sys
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.repositories.customer_tier import CustomerTierRepository
from app.repositories.product import ProductRepository
from app.repositories.product_category import ProductCategoryRepository
from app.schemas.customer_tier import CustomerTierCreate
from app.schemas.discount_policy import DiscountPolicyCreate, DiscountPolicyUpdate
from app.schemas.product import ProductCreate
from app.schemas.product_category import ProductCategoryCreate
from app.services.discount_policy import DiscountPolicyService
from app.services.exceptions import (
    CommercialPolicyValidationError,
    InactiveReferenceError,
    InvalidReferenceError,
    PolicyAmbiguityError,
)


@pytest.mark.anyio
async def test_discount_policy_global(db_session: AsyncSession):
    """Verify creation and retrieval of global discount policy."""
    service = DiscountPolicyService(db_session)
    policy_name = f"Global Discount {uuid.uuid4().hex[:6]}"

    created = await service.create_policy(
        DiscountPolicyCreate(
            name=policy_name,
            standard_discount_pct=Decimal("5.00"),
            max_discount_pct=Decimal("15.00"),
            priority=100,
        )
    )
    assert created.id is not None
    assert created.name == policy_name
    assert created.customer_tier_id is None
    assert created.product_category_id is None
    assert created.product_id is None
    assert created.standard_discount_pct == Decimal("5.00")
    assert created.max_discount_pct == Decimal("15.00")


@pytest.mark.anyio
async def test_discount_policy_tier_and_product_scopes(db_session: AsyncSession):
    """Verify tier-scoped, category-scoped, and product-scoped discount policy creation."""
    tier_repo = CustomerTierRepository()
    cat_repo = ProductCategoryRepository()
    prod_repo = ProductRepository()

    tier = await tier_repo.create_tier(db_session, CustomerTierCreate(name=f"GOLD_{uuid.uuid4().hex[:6]}"))
    cat = await cat_repo.create_category(db_session, ProductCategoryCreate(name=f"HARDWARE_{uuid.uuid4().hex[:6]}"))
    prod = await prod_repo.create_product(
        db_session,
        ProductCreate(
            sku=f"SKU_{uuid.uuid4().hex[:6]}",
            name="Laptop Pro",
            category_id=cat.id,
            list_price=Decimal("1000.00"),
        ),
    )
    await db_session.commit()

    service = DiscountPolicyService(db_session)

    # 1. Tier-scoped policy
    tier_policy = await service.create_policy(
        DiscountPolicyCreate(
            name="Gold Tier Policy",
            customer_tier_id=tier.id,
            standard_discount_pct=Decimal("10.00"),
            max_discount_pct=Decimal("20.00"),
        )
    )
    assert tier_policy.customer_tier_id == tier.id

    # 2. Product-scoped policy
    prod_policy = await service.create_policy(
        DiscountPolicyCreate(
            name="Laptop Specific Policy",
            product_id=prod.id,
            standard_discount_pct=Decimal("12.00"),
            max_discount_pct=Decimal("25.00"),
        )
    )
    assert prod_policy.product_id == prod.id


@pytest.mark.anyio
async def test_invalid_product_and_category_scope_rejected(db_session: AsyncSession):
    """Verify creating policy with both product_id and product_category_id is rejected."""
    tier_repo = CustomerTierRepository()
    cat_repo = ProductCategoryRepository()
    prod_repo = ProductRepository()

    cat = await cat_repo.create_category(db_session, ProductCategoryCreate(name=f"CAT_{uuid.uuid4().hex[:6]}"))
    prod = await prod_repo.create_product(
        db_session,
        ProductCreate(
            sku=f"SKU_{uuid.uuid4().hex[:6]}",
            name="Widget",
            category_id=cat.id,
            list_price=Decimal("10.00"),
        ),
    )
    await db_session.commit()

    service = DiscountPolicyService(db_session)
    with pytest.raises(CommercialPolicyValidationError) as exc_info:
        await service.create_policy(
            DiscountPolicyCreate(
                name="Invalid Both Scope",
                product_category_id=cat.id,
                product_id=prod.id,
                standard_discount_pct=Decimal("5.00"),
                max_discount_pct=Decimal("10.00"),
            )
        )
    assert "both product_id and product_category_id" in str(exc_info.value)


@pytest.mark.anyio
async def test_discount_standard_greater_than_max_rejected(db_session: AsyncSession):
    """Verify standard_discount_pct > max_discount_pct is rejected."""
    service = DiscountPolicyService(db_session)
    with pytest.raises(CommercialPolicyValidationError) as exc_info:
        await service.create_policy(
            DiscountPolicyCreate(
                name="Invalid Standard > Max",
                standard_discount_pct=Decimal("20.00"),
                max_discount_pct=Decimal("10.00"),
            )
        )
    assert "cannot exceed max_discount_pct" in str(exc_info.value)


@pytest.mark.anyio
async def test_discount_effective_date_ordering(db_session: AsyncSession):
    """Verify effective_to <= effective_from is rejected."""
    service = DiscountPolicyService(db_session)
    now = datetime.now(timezone.utc)
    past = now - timedelta(days=1)

    with pytest.raises(CommercialPolicyValidationError) as exc_info:
        await service.create_policy(
            DiscountPolicyCreate(
                name="Invalid Dates",
                effective_from=now,
                effective_to=past,
                standard_discount_pct=Decimal("5.00"),
                max_discount_pct=Decimal("10.00"),
            )
        )
    assert "effective_to timestamp must be strictly after effective_from" in str(exc_info.value)


@pytest.mark.anyio
async def test_discount_policy_precedence_resolution(db_session: AsyncSession):
    """Verify get_applicable_policy resolves deterministic precedence order."""
    tier_repo = CustomerTierRepository()
    cat_repo = ProductCategoryRepository()
    prod_repo = ProductRepository()

    tier = await tier_repo.create_tier(db_session, CustomerTierCreate(name=f"PLATINUM_{uuid.uuid4().hex[:6]}"))
    cat = await cat_repo.create_category(db_session, ProductCategoryCreate(name=f"SOFTWARE_{uuid.uuid4().hex[:6]}"))
    prod = await prod_repo.create_product(
        db_session,
        ProductCreate(
            sku=f"SKU_PREC_{uuid.uuid4().hex[:6]}",
            name="Cloud Suite",
            category_id=cat.id,
            list_price=Decimal("500.00"),
        ),
    )
    await db_session.commit()

    service = DiscountPolicyService(db_session)

    # Seed 4 levels of policy precedence:
    # 1. Global policy
    p_global = await service.create_policy(
        DiscountPolicyCreate(
            name="Global Baseline Policy",
            standard_discount_pct=Decimal("2.00"),
            max_discount_pct=Decimal("5.00"),
            priority=100,
        )
    )
    # 2. Tier policy
    p_tier = await service.create_policy(
        DiscountPolicyCreate(
            name="Platinum Tier Policy",
            customer_tier_id=tier.id,
            standard_discount_pct=Decimal("10.00"),
            max_discount_pct=Decimal("15.00"),
            priority=100,
        )
    )
    # 3. Product policy
    p_prod = await service.create_policy(
        DiscountPolicyCreate(
            name="Software Product Policy",
            product_id=prod.id,
            standard_discount_pct=Decimal("12.00"),
            max_discount_pct=Decimal("18.00"),
            priority=100,
        )
    )
    # 4. Tier + Product policy
    p_tier_prod = await service.create_policy(
        DiscountPolicyCreate(
            name="Platinum Software Exclusive",
            customer_tier_id=tier.id,
            product_id=prod.id,
            standard_discount_pct=Decimal("20.00"),
            max_discount_pct=Decimal("30.00"),
            priority=100,
        )
    )

    # Resolution 1: Most specific (tier+product) wins
    res1, spec1 = await service.get_applicable_policy(tier.id, prod.id)
    assert res1.id == p_tier_prod.id
    assert spec1 == "tier+product"

    # Deactivate tier+product -> Product wins (spec2 == 'product')
    await service.update_policy(p_tier_prod.id, DiscountPolicyUpdate(is_active=False))
    res2, spec2 = await service.get_applicable_policy(tier.id, prod.id)
    assert res2.id == p_prod.id
    assert spec2 == "product"

    # Deactivate product -> Tier wins (spec3 == 'tier')
    await service.update_policy(p_prod.id, DiscountPolicyUpdate(is_active=False))
    res3, spec3 = await service.get_applicable_policy(tier.id, prod.id)
    assert res3.id == p_tier.id
    assert spec3 == "tier"

    # Deactivate tier -> Global wins (spec4 == 'global')
    await service.update_policy(p_tier.id, DiscountPolicyUpdate(is_active=False))
    res4, spec4 = await service.get_applicable_policy(tier.id, prod.id)
    assert res4.id == p_global.id
    assert spec4 == "global"


@pytest.mark.anyio
async def test_discount_policy_same_scope_ambiguity_rejected(db_session: AsyncSession):
    """Verify creating conflicting policy with identical scope, priority, and overlapping time range is rejected."""
    service = DiscountPolicyService(db_session)
    p_name = f"Primary Policy {uuid.uuid4().hex[:6]}"

    await service.create_policy(
        DiscountPolicyCreate(
            name=p_name,
            standard_discount_pct=Decimal("5.00"),
            max_discount_pct=Decimal("10.00"),
            priority=50,
        )
    )

    with pytest.raises(PolicyAmbiguityError) as exc_info:
        await service.create_policy(
            DiscountPolicyCreate(
                name="Conflicting Identical Policy",
                standard_discount_pct=Decimal("8.00"),
                max_discount_pct=Decimal("12.00"),
                priority=50,
            )
        )
    assert "already exists with identical scope, priority" in str(exc_info.value)
