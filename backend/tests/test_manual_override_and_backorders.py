import pytest
from decimal import Decimal
from sqlalchemy import select

from app.core.enums import QuotationStatus
from app.core.roles import RoleName
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.quotation import Quotation
from app.models.quotation_line import QuoteLine
from app.models.role import Role
from app.models.user import User
from app.models.warehouse import Warehouse
from app.services.fulfillment import FulfillmentService
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
async def test_manual_fulfillment_override(db_session):
    role_admin = await get_or_create_role(db_session, RoleName.ADMIN)
    role_rep = await get_or_create_role(db_session, RoleName.SALES_REP)
    tier = CustomerTier(name="Override Tier")
    cat = ProductCategory(name="Override Cat")
    db_session.add_all([tier, cat])
    await db_session.flush()

    admin = User(email="admin_over@example.com", hashed_password="pw", full_name="Admin Over", role_id=role_admin.id)
    rep = User(email="rep_over@example.com", hashed_password="pw", full_name="Rep Over", role_id=role_rep.id)
    cust = Customer(customer_code="OVER-CUST-1", name="Override Corp", email="over@corp.com", tier_id=tier.id)
    db_session.add_all([admin, rep, cust])
    await db_session.flush()

    prod = Product(sku="OVER-P1", name="Override Prod", category_id=cat.id, list_price=Decimal("100.00"), cost_price=Decimal("50.00"))
    wh1 = Warehouse(code="WH-O1", name="Warehouse 1", fulfillment_priority=1, is_active=True)
    wh2 = Warehouse(code="WH-O2", name="Warehouse 2", fulfillment_priority=2, is_active=True)
    db_session.add_all([prod, wh1, wh2])
    await db_session.flush()

    inv1 = Inventory(warehouse_id=wh1.id, product_id=prod.id, on_hand_qty=Decimal("10"), reserved_qty=Decimal("0"))
    inv2 = Inventory(warehouse_id=wh2.id, product_id=prod.id, on_hand_qty=Decimal("20"), reserved_qty=Decimal("0"))
    db_session.add_all([inv1, inv2])
    await db_session.flush()

    quote = Quotation(
        quote_number="Q-OVER-1",
        customer_id=cust.id,
        sales_rep_id=rep.id,
        currency="USD",
        payment_terms_days=30,
        status=QuotationStatus.CUSTOMER_CONFIRMED.value,
        gross_subtotal=Decimal("100.00"),
        net_total=Decimal("100.00"),
        total_cost=Decimal("50.00"),
        margin_amount=Decimal("50.00"),
        margin_pct=Decimal("50.00"),
    )
    db_session.add(quote)
    await db_session.flush()

    line = QuoteLine(
        quotation_id=quote.id,
        product_id=prod.id,
        quantity=Decimal("5"),
        unit_list_price=Decimal("100.00"),
        unit_cost=Decimal("50.00"),
        gross_line_total=Decimal("100.00"),
        net_line_total=Decimal("100.00"),
        line_cost=Decimal("50.00"),
        margin_amount=Decimal("50.00"),
        margin_pct=Decimal("50.00"),
    )
    db_session.add(line)
    await db_session.flush()

    v_service = QuoteVersionService(db_session)
    v1 = await v_service.create_version_snapshot(quote.id, "INITIAL_RELEASE", rep.id)
    quote.confirmed_quote_version_id = v1.id
    await db_session.commit()

    order_service = OrderService(db_session)
    order = await order_service.create_order_from_confirmed_quotation(quote.id, rep.id)

    fulfillment_service = FulfillmentService(db_session)
    # Automatic allocation reserves 5 from WH1
    plan = await fulfillment_service.generate_optimal_fulfillment_plan(order.id, admin.id)

    order_line_id = order.lines[0].id
    override_payload = {
        "override_reason": "Customer requested dispatch from WH2",
        "allocations": [
            {"order_line_id": order_line_id, "warehouse_id": wh2.id, "allocated_qty": 5.0}
        ]
    }

    overridden_plan = await fulfillment_service.apply_manual_fulfillment_override(order.id, override_payload, admin.id)
    assert overridden_plan.is_manually_overridden is True
    assert len(overridden_plan.allocations) == 1
    assert overridden_plan.allocations[0].warehouse_id == wh2.id
    assert overridden_plan.allocations[0].allocated_qty == Decimal("5")
