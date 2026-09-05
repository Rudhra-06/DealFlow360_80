import pytest
from decimal import Decimal
from sqlalchemy import select

from app.core.enums import QuotationStatus
from app.core.roles import RoleName
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.quotation import Quotation
from app.models.quotation_line import QuoteLine
from app.models.role import Role
from app.models.user import User
from app.services.order import OrderService
from app.services.quote_version import QuoteVersionService


async def get_or_create_role(db, name):
    res = await db.execute(select(Role).where(Role.name == name))
    r = res.scalar_one_or_none()
    if not r:
        r = Role(name=name, description=name)
        db.add(r)
        await db.flush()
    return r


@pytest.mark.asyncio
async def test_sales_order_creation_from_quote(db_session):
    role_rep = await get_or_create_role(db_session, RoleName.SALES_REP)
    tier = CustomerTier(name="Order Tier")
    cat = ProductCategory(name="Order Cat")
    db_session.add_all([tier, cat])
    await db_session.flush()

    rep = User(email="order_rep@example.com", hashed_password="pw", full_name="Order Rep", role_id=role_rep.id)
    cust = Customer(customer_code="ORD-CUST-1", name="Order Corp", email="ord@corp.com", tier_id=tier.id)
    db_session.add_all([rep, cust])
    await db_session.flush()

    prod = Product(sku="ORD-P1", name="Order Prod", category_id=cat.id, list_price=Decimal("150.00"), cost_price=Decimal("80.00"))
    db_session.add(prod)
    await db_session.flush()

    quote = Quotation(
        quote_number="Q-ORD-100",
        customer_id=cust.id,
        sales_rep_id=rep.id,
        currency="USD",
        payment_terms_days=30,
        status=QuotationStatus.CUSTOMER_CONFIRMED.value,
        gross_subtotal=Decimal("150.00"),
        net_total=Decimal("150.00"),
        total_cost=Decimal("80.00"),
        margin_amount=Decimal("70.00"),
        margin_pct=Decimal("46.67"),
    )
    db_session.add(quote)
    await db_session.flush()

    line = QuoteLine(
        quotation_id=quote.id,
        product_id=prod.id,
        quantity=Decimal("2"),
        unit_list_price=Decimal("75.00"),
        unit_cost=Decimal("40.00"),
        gross_line_total=Decimal("150.00"),
        net_line_total=Decimal("150.00"),
        line_cost=Decimal("80.00"),
        margin_amount=Decimal("70.00"),
        margin_pct=Decimal("46.67"),
    )
    db_session.add(line)
    await db_session.flush()

    v_service = QuoteVersionService(db_session)
    v1 = await v_service.create_version_snapshot(quote.id, "INITIAL_RELEASE", rep.id)
    quote.confirmed_quote_version_id = v1.id
    await db_session.commit()

    order_service = OrderService(db_session)
    order = await order_service.create_order_from_confirmed_quotation(quote.id, rep.id)

    assert order.id is not None
    assert order.order_number.startswith("SO-")
    assert order.quotation_id == quote.id
    assert order.confirmed_version_id == v1.id
    assert order.status == "FULFILLMENT"
    assert len(order.lines) == 1
    assert order.lines[0].product_id == prod.id
    assert order.lines[0].ordered_qty == Decimal("2")
