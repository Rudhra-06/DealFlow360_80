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
from app.services.customer_portal_access import CustomerPortalAccessService
from app.services.exceptions import QuoteAccessDeniedError
from app.services.portal_quotation import PortalQuotationService


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
async def test_customer_portal_access_service(db_session):
    role_cust = await get_or_create_role(db_session, RoleName.CUSTOMER)
    role_rep = await get_or_create_role(db_session, RoleName.SALES_REP)
    tier = await get_or_create_tier(db_session)

    user_cust = User(email="cust1@example.com", hashed_password="pw", full_name="Customer User 1", role_id=role_cust.id)
    user_other = User(email="cust2@example.com", hashed_password="pw", full_name="Customer User 2", role_id=role_cust.id)
    user_rep = User(email="rep@example.com", hashed_password="pw", full_name="Sales Rep", role_id=role_rep.id)
    db_session.add_all([user_cust, user_other, user_rep])
    await db_session.flush()

    customer = Customer(customer_code="CUST-SEC-1", name="Acme Corp", email="contact@acme.com", tier_id=tier.id)
    db_session.add(customer)
    await db_session.flush()

    access_service = CustomerPortalAccessService(db_session)
    from app.schemas.customer_portal_access import CustomerPortalAccessCreate

    access = await access_service.create_access(
        CustomerPortalAccessCreate(user_id=user_cust.id, customer_id=customer.id, is_active=True)
    )
    assert access.user_id == user_cust.id
    assert access.customer_id == customer.id

    cust_id = await access_service.get_active_customer_id_for_user(user_cust.id)
    assert cust_id == customer.id

    with pytest.raises(QuoteAccessDeniedError):
        await access_service.get_active_customer_id_for_user(user_other.id)


@pytest.mark.asyncio
async def test_portal_safe_quotation_representation(db_session):
    role_cust = await get_or_create_role(db_session, RoleName.CUSTOMER)
    role_rep = await get_or_create_role(db_session, RoleName.SALES_REP)
    tier = await get_or_create_tier(db_session)
    cat = await get_or_create_category(db_session)

    user_cust = User(email="cust_safe@example.com", hashed_password="pw", full_name="Cust Safe", role_id=role_cust.id)
    user_rep = User(email="rep_safe@example.com", hashed_password="pw", full_name="Rep Safe", role_id=role_rep.id)
    db_session.add_all([user_cust, user_rep])
    await db_session.flush()

    customer = Customer(customer_code="CUST-SEC-2", name="Beta Corp", email="info@beta.com", tier_id=tier.id)
    db_session.add(customer)
    await db_session.flush()

    c_access = CustomerPortalAccess(user_id=user_cust.id, customer_id=customer.id, is_active=True)
    db_session.add(c_access)

    prod = Product(sku="SAFE-01", name="Safe Prod", category_id=cat.id, list_price=Decimal("100.00"), cost_price=Decimal("40.00"))
    db_session.add(prod)
    await db_session.flush()

    quote = Quotation(
        quote_number="Q-SAFE-001",
        customer_id=customer.id,
        sales_rep_id=user_rep.id,
        currency="USD",
        payment_terms_days=30,
        status=QuotationStatus.SENT_TO_CUSTOMER.value,
        gross_subtotal=Decimal("100.00"),
        discount_amount=Decimal("10.00"),
        net_total=Decimal("90.00"),
        total_cost=Decimal("40.00"),
        margin_amount=Decimal("50.00"),
        margin_pct=Decimal("55.56"),
        blended_risk_score=Decimal("10.00"),
        risk_level="GREEN",
    )
    db_session.add(quote)
    await db_session.flush()

    line = QuoteLine(
        quotation_id=quote.id,
        product_id=prod.id,
        quantity=Decimal("1"),
        unit_list_price=Decimal("100.00"),
        unit_cost=Decimal("40.00"),
        line_discount_pct=Decimal("10.00"),
        effective_discount_pct=Decimal("10.00"),
        gross_line_total=Decimal("100.00"),
        discount_amount=Decimal("10.00"),
        net_line_total=Decimal("90.00"),
        line_cost=Decimal("40.00"),
        margin_amount=Decimal("50.00"),
        margin_pct=Decimal("55.56"),
        risk_level="GREEN",
    )
    db_session.add(line)
    await db_session.commit()

    portal_service = PortalQuotationService(db_session)
    p_quote = await portal_service.get_portal_quotation(quote.id, user_cust.id)

    assert p_quote.quote_number == "Q-SAFE-001"
    assert p_quote.customer_id == customer.id
