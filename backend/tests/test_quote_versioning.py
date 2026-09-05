import pytest
from decimal import Decimal
from sqlalchemy import select

from app.core.enums import QuotationStatus, VersionSourceType
from app.core.roles import RoleName
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.quotation import Quotation
from app.models.quotation_line import QuoteLine
from app.models.role import Role
from app.models.user import User
from app.services.quote_version import QuoteVersionService


async def get_or_create_role(db_session, role_name: str):
    res = await db_session.execute(select(Role).where(Role.name == role_name))
    role = res.scalar_one_or_none()
    if not role:
        role = Role(name=role_name, description=role_name)
        db_session.add(role)
        await db_session.flush()
    return role


async def get_or_create_tier(db_session):
    res = await db_session.execute(select(CustomerTier))
    tier = res.scalars().first()
    if not tier:
        tier = CustomerTier(name="Standard Tier", description="Standard Tier")
        db_session.add(tier)
        await db_session.flush()
    return tier


async def get_or_create_category(db_session):
    res = await db_session.execute(select(ProductCategory))
    cat = res.scalars().first()
    if not cat:
        cat = ProductCategory(name="General Category")
        db_session.add(cat)
        await db_session.flush()
    return cat


@pytest.mark.asyncio
async def test_quote_version_creation_and_diff(db_session):
    role_rep = await get_or_create_role(db_session, RoleName.SALES_REP)
    tier = await get_or_create_tier(db_session)
    cat = await get_or_create_category(db_session)

    user_rep = User(email="rep_v@example.com", hashed_password="pw", full_name="Rep V", role_id=role_rep.id)
    customer = Customer(customer_code="CUST-VER-1", name="Version Corp", email="v@corp.com", tier_id=tier.id)
    prod1 = Product(sku="V-PROD-1", name="Product 1", category_id=cat.id, list_price=Decimal("200.00"), cost_price=Decimal("100.00"))
    prod2 = Product(sku="V-PROD-2", name="Product 2", category_id=cat.id, list_price=Decimal("300.00"), cost_price=Decimal("150.00"))
    db_session.add_all([user_rep, customer, prod1, prod2])
    await db_session.flush()

    quote = Quotation(
        quote_number="Q-VER-001",
        customer_id=customer.id,
        sales_rep_id=user_rep.id,
        currency="USD",
        payment_terms_days=30,
        order_discount_pct=Decimal("0.00"),
        status=QuotationStatus.APPROVED.value,
        gross_subtotal=Decimal("200.00"),
        discount_amount=Decimal("0.00"),
        net_total=Decimal("200.00"),
        total_cost=Decimal("100.00"),
        margin_amount=Decimal("100.00"),
        margin_pct=Decimal("50.00"),
        weighted_effective_discount_pct=Decimal("0.00"),
        blended_risk_score=Decimal("10.00"),
        risk_level="GREEN",
    )
    db_session.add(quote)
    await db_session.flush()

    line1 = QuoteLine(
        quotation_id=quote.id,
        product_id=prod1.id,
        quantity=Decimal("1"),
        unit_list_price=Decimal("200.00"),
        unit_cost=Decimal("100.00"),
        line_discount_pct=Decimal("0.00"),
        effective_discount_pct=Decimal("0.00"),
        gross_line_total=Decimal("200.00"),
        discount_amount=Decimal("0.00"),
        net_line_total=Decimal("200.00"),
        line_cost=Decimal("100.00"),
        margin_amount=Decimal("100.00"),
        margin_pct=Decimal("50.00"),
        risk_level="GREEN",
    )
    db_session.add(line1)
    await db_session.commit()

    version_service = QuoteVersionService(db_session)
    v1 = await version_service.create_version_snapshot(
        quotation_id=quote.id,
        source_type=VersionSourceType.INITIAL_RELEASE.value,
        created_by_user_id=user_rep.id,
    )
    assert v1.version_number == 1
    assert len(v1.lines) == 1
    assert v1.net_total == Decimal("200.00")

    # Modify quotation terms & add line for v2
    quote.order_discount_pct = Decimal("5.00")
    quote.payment_terms_days = 45
    quote.gross_subtotal = Decimal("500.00")
    quote.discount_amount = Decimal("25.00")
    quote.net_total = Decimal("475.00")

    line2 = QuoteLine(
        quotation_id=quote.id,
        product_id=prod2.id,
        quantity=Decimal("1"),
        unit_list_price=Decimal("300.00"),
        unit_cost=Decimal("150.00"),
        line_discount_pct=Decimal("0.00"),
        effective_discount_pct=Decimal("5.00"),
        gross_line_total=Decimal("300.00"),
        discount_amount=Decimal("15.00"),
        net_line_total=Decimal("285.00"),
        line_cost=Decimal("150.00"),
        margin_amount=Decimal("135.00"),
        margin_pct=Decimal("47.37"),
        risk_level="GREEN",
    )
    db_session.add(line2)
    await db_session.commit()

    v2 = await version_service.create_version_snapshot(
        quotation_id=quote.id,
        source_type=VersionSourceType.CUSTOMER_COUNTER_ACCEPTED.value,
        created_by_user_id=user_rep.id,
    )
    assert v2.version_number == 2
    assert len(v2.lines) == 2

    # Compare versions
    diff = await version_service.compare_versions(quote.id, 1, 2)
    assert diff.from_version_number == 1
    assert diff.to_version_number == 2
    assert diff.header_changes["payment_terms_days"]["from"] == 30
    assert diff.header_changes["payment_terms_days"]["to"] == 45
    assert len(diff.added_lines) == 1
    assert diff.added_lines[0]["product_sku_snapshot"] == "V-PROD-2"
