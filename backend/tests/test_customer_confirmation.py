import pytest
from decimal import Decimal
from sqlalchemy import select

from app.core.enums import QuotationStatus
from app.core.roles import RoleName
from app.models.customer import Customer
from app.models.customer_portal_access import CustomerPortalAccess
from app.models.customer_tier import CustomerTier
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.quotation import Quotation
from app.models.quotation_line import QuoteLine
from app.models.role import Role
from app.models.user import User
from app.services.portal_quotation import PortalQuotationService
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
async def test_customer_confirmation_flow(db_session):
    role_cust = await get_or_create_role(db_session, RoleName.CUSTOMER)
    role_rep = await get_or_create_role(db_session, RoleName.SALES_REP)
    tier = await get_or_create_tier(db_session)
    cat = await get_or_create_category(db_session)

    user_cust = User(email="cust_conf@example.com", hashed_password="pw", full_name="Cust Conf", role_id=role_cust.id)
    user_rep = User(email="rep_conf@example.com", hashed_password="pw", full_name="Rep Conf", role_id=role_rep.id)
    customer = Customer(customer_code="CUST-CONF-1", name="Confirm Corp", email="c@corp.com", tier_id=tier.id)
    db_session.add_all([user_cust, user_rep, customer])
    await db_session.flush()

    access = CustomerPortalAccess(user_id=user_cust.id, customer_id=customer.id, is_active=True)
    db_session.add(access)

    prod = Product(sku="CONF-1", name="Confirm Prod", category_id=cat.id, list_price=Decimal("100.00"), cost_price=Decimal("50.00"))
    db_session.add(prod)
    await db_session.flush()

    quote = Quotation(
        quote_number="Q-CONF-001",
        customer_id=customer.id,
        sales_rep_id=user_rep.id,
        currency="USD",
        payment_terms_days=30,
        order_discount_pct=Decimal("0.00"),
        status=QuotationStatus.SENT_TO_CUSTOMER.value,
        gross_subtotal=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        net_total=Decimal("100.00"),
        total_cost=Decimal("50.00"),
        margin_amount=Decimal("50.00"),
        margin_pct=Decimal("50.00"),
        weighted_effective_discount_pct=Decimal("0.00"),
        blended_risk_score=Decimal("5.00"),
        risk_level="GREEN",
    )
    db_session.add(quote)
    await db_session.flush()

    line = QuoteLine(
        quotation_id=quote.id,
        product_id=prod.id,
        quantity=Decimal("1"),
        unit_list_price=Decimal("100.00"),
        unit_cost=Decimal("50.00"),
        line_discount_pct=Decimal("0.00"),
        effective_discount_pct=Decimal("0.00"),
        gross_line_total=Decimal("100.00"),
        discount_amount=Decimal("0.00"),
        net_line_total=Decimal("100.00"),
        line_cost=Decimal("50.00"),
        margin_amount=Decimal("50.00"),
        margin_pct=Decimal("50.00"),
        risk_level="GREEN",
    )
    db_session.add(line)
    await db_session.commit()

    v_service = QuoteVersionService(db_session)
    v1 = await v_service.create_version_snapshot(quote.id, "INITIAL_RELEASE", user_rep.id)
    quote.current_version_id = v1.id
    await db_session.commit()

    portal_service = PortalQuotationService(db_session)
    confirmed_quote = await portal_service.confirm_quotation(quote.id, user_cust.id)

    assert confirmed_quote.status == QuotationStatus.CUSTOMER_ACCEPTED.value
    assert confirmed_quote.confirmed_quote_version_id == v1.id
    assert confirmed_quote.customer_confirmed_by_user_id == user_cust.id
    assert confirmed_quote.customer_confirmed_at is not None
