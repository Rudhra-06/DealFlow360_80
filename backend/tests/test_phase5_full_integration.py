import pytest
from decimal import Decimal
from sqlalchemy import select

from app.core.enums import QuotationStatus
from app.core.roles import RoleName
from app.models.billing_plan import BillingPlan
from app.models.customer import Customer
from app.models.customer_portal_access import CustomerPortalAccess
from app.models.customer_tier import CustomerTier
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.quotation import Quotation
from app.models.quotation_line import QuoteLine
from app.models.role import Role
from app.models.user import User
from app.models.warehouse import Warehouse
from app.services.billing import BillingService
from app.services.fulfillment import FulfillmentService
from app.services.order import OrderService
from app.services.payment import PaymentService
from app.services.portal_quotation import PortalQuotationService
from app.services.quote_version import QuoteVersionService
from app.services.shipment import ShipmentService
from app.services.subscription import SubscriptionService


async def get_or_create_role(db, name):
    res = await db.execute(select(Role).where(Role.name == name))
    r = res.scalar_one_or_none()
    if not r:
        r = Role(name=name, description=name)
        db.add(r)
        await db.flush()
    return r


@pytest.mark.asyncio
async def test_phase5_full_order_to_cash_end_to_end(db_session):
    role_admin = await get_or_create_role(db_session, RoleName.ADMIN)
    role_rep = await get_or_create_role(db_session, RoleName.SALES_REP)
    role_cust = await get_or_create_role(db_session, RoleName.CUSTOMER)

    tier = CustomerTier(name="E2E Tier")
    cat = ProductCategory(name="E2E Cat")
    plan = BillingPlan(
        code="BP-MONTHLY-E2E",
        name="E2E Monthly Plan",
        billing_type="RECURRING",
        billing_interval_months=1,
        proration_method="DAILY",
        cancellation_method="END_OF_PERIOD",
        is_active=True,
    )
    db_session.add_all([tier, cat, plan])
    await db_session.flush()

    admin = User(email="admin_e2e@example.com", hashed_password="pw", full_name="Admin E2E", role_id=role_admin.id)
    rep = User(email="rep_e2e@example.com", hashed_password="pw", full_name="Rep E2E", role_id=role_rep.id)
    cust_user = User(email="cust_e2e@example.com", hashed_password="pw", full_name="Cust E2E User", role_id=role_cust.id)
    customer = Customer(customer_code="E2E-CUST-1", name="E2E Enterprise", email="e2e@corp.com", tier_id=tier.id)
    db_session.add_all([admin, rep, cust_user, customer])
    await db_session.flush()

    access = CustomerPortalAccess(user_id=cust_user.id, customer_id=customer.id, is_active=True)
    db_session.add(access)

    prod_hw = Product(sku="E2E-HW", name="Hardware Device", category_id=cat.id, list_price=Decimal("1000.00"), cost_price=Decimal("400.00"))
    prod_sw = Product(sku="E2E-SW", name="Software Subscription", category_id=cat.id, list_price=Decimal("200.00"), cost_price=Decimal("20.00"))
    wh = Warehouse(code="WH-E2E", name="E2E Warehouse", fulfillment_priority=1, is_active=True)
    db_session.add_all([prod_hw, prod_sw, wh])
    await db_session.flush()

    inv_hw = Inventory(warehouse_id=wh.id, product_id=prod_hw.id, on_hand_qty=Decimal("10"), reserved_qty=Decimal("0"))
    inv_sw = Inventory(warehouse_id=wh.id, product_id=prod_sw.id, on_hand_qty=Decimal("100"), reserved_qty=Decimal("0"))
    db_session.add_all([inv_hw, inv_sw])
    await db_session.flush()

    quote = Quotation(
        quote_number="Q-E2E-999",
        customer_id=customer.id,
        sales_rep_id=rep.id,
        currency="USD",
        payment_terms_days=30,
        status=QuotationStatus.SENT_TO_CUSTOMER.value,
        gross_subtotal=Decimal("1200.00"),
        net_total=Decimal("1200.00"),
        total_cost=Decimal("420.00"),
        margin_amount=Decimal("780.00"),
        margin_pct=Decimal("65.00"),
    )
    db_session.add(quote)
    await db_session.flush()

    line_hw = QuoteLine(
        quotation_id=quote.id,
        product_id=prod_hw.id,
        quantity=Decimal("1"),
        unit_list_price=Decimal("1000.00"),
        unit_cost=Decimal("400.00"),
        gross_line_total=Decimal("1000.00"),
        net_line_total=Decimal("1000.00"),
        line_cost=Decimal("400.00"),
        margin_amount=Decimal("600.00"),
        margin_pct=Decimal("60.00"),
    )
    line_sw = QuoteLine(
        quotation_id=quote.id,
        product_id=prod_sw.id,
        quantity=Decimal("1"),
        unit_list_price=Decimal("200.00"),
        unit_cost=Decimal("20.00"),
        gross_line_total=Decimal("200.00"),
        net_line_total=Decimal("200.00"),
        line_cost=Decimal("20.00"),
        margin_amount=Decimal("180.00"),
        margin_pct=Decimal("90.00"),
        billing_plan_id=plan.id,
    )
    db_session.add_all([line_hw, line_sw])
    await db_session.flush()

    v_service = QuoteVersionService(db_session)
    v1 = await v_service.create_version_snapshot(quote.id, "INITIAL_RELEASE", rep.id)
    quote.current_version_id = v1.id
    await db_session.commit()

    # STEP 1: Customer confirms quotation via portal
    portal_service = PortalQuotationService(db_session)
    confirmed_quote = await portal_service.confirm_quotation(quote.id, cust_user.id)
    assert confirmed_quote.status == QuotationStatus.CUSTOMER_CONFIRMED.value

    # Verify auto-created sales order
    order_service = OrderService(db_session)
    order = await order_service.get_order_by_quotation(quote.id)
    assert order is not None
    assert order.status == "FULFILLMENT"

    # STEP 2: Intelligent Multi-Warehouse Fulfillment & Reservation
    fulfillment_service = FulfillmentService(db_session)
    plan_obj = await fulfillment_service.generate_optimal_fulfillment_plan(order.id, admin.id)
    assert plan_obj.id is not None
    assert inv_hw.reserved_qty == Decimal("1")
    assert inv_sw.reserved_qty == Decimal("1")

    # STEP 3: Shipment Execution & Stock Consumption
    shipment_service = ShipmentService(db_session)
    hw_order_line = next(l for l in order.lines if l.product_id == prod_hw.id)
    shipment_payload = {
        "sales_order_id": order.id,
        "warehouse_id": wh.id,
        "carrier": "DHL Express",
        "tracking_number": "DHL-E2E-777",
        "lines": [
            {"sales_order_line_id": hw_order_line.id, "shipped_qty": 1.0}
        ]
    }
    shipment = await shipment_service.create_and_process_shipment(shipment_payload, admin.id)
    assert shipment.status == "SHIPPED"
    assert inv_hw.on_hand_qty == Decimal("9")
    assert inv_hw.reserved_qty == Decimal("0")

    # STEP 4: Billing & Subscriptions Initialization
    billing_service = BillingService(db_session)
    invoices = await billing_service.invoice_repo.list_by_order(db_session, order.id)
    assert len(invoices) >= 1
    hw_invoice = next(i for i in invoices if i.invoice_type == "ONE_TIME")
    assert hw_invoice.total_amount == Decimal("1000.00")

    sub_service = SubscriptionService(db_session)
    subs = await sub_service.sub_repo.list_subscriptions(db_session, sales_order_id=order.id)
    assert len(subs) == 1
    assert subs[0].monthly_recurring_revenue == Decimal("200.00")

    # STEP 5: Payment Recording & Invoice Balance Allocation
    payment_service = PaymentService(db_session)
    payment = await payment_service.record_payment(
        customer_id=customer.id,
        amount=1000.0,
        currency="USD",
        payment_method="BANK_TRANSFER",
        allocations_input=[{"invoice_id": hw_invoice.id, "amount": 1000.0}],
        recorded_by_user_id=admin.id,
        reference="WIRE-E2E-1000",
    )
    assert payment.id is not None
    updated_hw_invoice = await billing_service.invoice_repo.get_by_id(db_session, hw_invoice.id)
    assert updated_hw_invoice.status == "PAID"
    assert updated_hw_invoice.balance_due == Decimal("0.00")
