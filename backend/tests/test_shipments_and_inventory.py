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
from app.services.shipment import ShipmentService


async def get_or_create_role(db, name):
    res = await db.execute(select(Role).where(Role.name == name))
    r = res.scalar_one_or_none()
    if not r:
        r = Role(name=name, description=name)
        db.add(r)
        await db.flush()
    return r


@pytest.mark.asyncio
async def test_shipment_execution_and_stock_consumption(db_session):
    role_admin = await get_or_create_role(db_session, RoleName.ADMIN)
    role_rep = await get_or_create_role(db_session, RoleName.SALES_REP)
    tier = CustomerTier(name="Ship Tier")
    cat = ProductCategory(name="Ship Cat")
    db_session.add_all([tier, cat])
    await db_session.flush()

    admin = User(email="admin_ship@example.com", hashed_password="pw", full_name="Admin Ship", role_id=role_admin.id)
    rep = User(email="rep_ship@example.com", hashed_password="pw", full_name="Rep Ship", role_id=role_rep.id)
    cust = Customer(customer_code="SHIP-CUST-1", name="Ship Corp", email="ship@corp.com", tier_id=tier.id)
    db_session.add_all([admin, rep, cust])
    await db_session.flush()

    prod = Product(sku="SHIP-P1", name="Ship Prod", category_id=cat.id, list_price=Decimal("200.00"), cost_price=Decimal("100.00"))
    wh = Warehouse(code="WH-S1", name="Ship Warehouse", fulfillment_priority=1, is_active=True)
    db_session.add_all([prod, wh])
    await db_session.flush()

    inv = Inventory(warehouse_id=wh.id, product_id=prod.id, on_hand_qty=Decimal("50"), reserved_qty=Decimal("0"))
    db_session.add(inv)
    await db_session.flush()

    quote = Quotation(
        quote_number="Q-SHIP-1",
        customer_id=cust.id,
        sales_rep_id=rep.id,
        currency="USD",
        payment_terms_days=30,
        status=QuotationStatus.CUSTOMER_CONFIRMED.value,
        gross_subtotal=Decimal("200.00"),
        net_total=Decimal("200.00"),
        total_cost=Decimal("100.00"),
        margin_amount=Decimal("100.00"),
        margin_pct=Decimal("50.00"),
    )
    db_session.add(quote)
    await db_session.flush()

    line = QuoteLine(
        quotation_id=quote.id,
        product_id=prod.id,
        quantity=Decimal("10"),
        unit_list_price=Decimal("20.00"),
        unit_cost=Decimal("10.00"),
        gross_line_total=Decimal("200.00"),
        net_line_total=Decimal("200.00"),
        line_cost=Decimal("100.00"),
        margin_amount=Decimal("100.00"),
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
    plan = await fulfillment_service.generate_optimal_fulfillment_plan(order.id, admin.id)

    assert inv.reserved_qty == Decimal("10")
    assert inv.on_hand_qty == Decimal("50")

    shipment_service = ShipmentService(db_session)
    shipment_payload = {
        "sales_order_id": order.id,
        "warehouse_id": wh.id,
        "carrier": "FedEx",
        "tracking_number": "TRACK123456",
        "lines": [
            {"sales_order_line_id": order.lines[0].id, "shipped_qty": 10.0}
        ]
    }

    shipment = await shipment_service.create_and_process_shipment(shipment_payload, admin.id)

    assert shipment.status == "SHIPPED"
    assert inv.on_hand_qty == Decimal("40")
    assert inv.reserved_qty == Decimal("0")
    assert order.lines[0].shipped_qty == Decimal("10")
    assert order.status in {"PARTIALLY_SHIPPED", "SHIPPED", "FULL_FULFILLED", "FULFILLED"}
