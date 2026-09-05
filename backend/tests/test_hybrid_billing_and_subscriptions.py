import pytest
from decimal import Decimal
from sqlalchemy import select

from app.core.enums import QuotationStatus
from app.core.roles import RoleName
from app.models.billing_plan import BillingPlan
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.quotation import Quotation
from app.models.quotation_line import QuoteLine
from app.models.role import Role
from app.models.user import User
from app.services.billing import BillingService
from app.services.order import OrderService
from app.services.quote_version import QuoteVersionService
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
async def test_hybrid_order_one_time_and_recurring_billing(db_session):
    role_admin = await get_or_create_role(db_session, RoleName.ADMIN)
    role_rep = await get_or_create_role(db_session, RoleName.SALES_REP)
    tier = CustomerTier(name="Hybrid Tier")
    cat = ProductCategory(name="Hybrid Cat")
    plan = BillingPlan(
        code="BP-MONTHLY-HYB",
        name="Monthly SaaS Plan",
        billing_type="RECURRING",
        billing_interval_months=1,
        proration_method="DAILY",
        cancellation_method="END_OF_PERIOD",
        is_active=True,
    )
    db_session.add_all([tier, cat, plan])
    await db_session.flush()

    admin = User(email="admin_hyb@example.com", hashed_password="pw", full_name="Admin Hyb", role_id=role_admin.id)
    rep = User(email="rep_hyb@example.com", hashed_password="pw", full_name="Rep Hyb", role_id=role_rep.id)
    cust = Customer(customer_code="HYB-CUST-1", name="Hybrid Corp", email="hyb@corp.com", tier_id=tier.id)
    db_session.add_all([admin, rep, cust])
    await db_session.flush()

    prod_onetime = Product(sku="HYB-HW", name="Hardware Product", category_id=cat.id, list_price=Decimal("500.00"), cost_price=Decimal("250.00"))
    prod_sub = Product(sku="HYB-SW", name="SaaS License", category_id=cat.id, list_price=Decimal("100.00"), cost_price=Decimal("10.00"))
    db_session.add_all([prod_onetime, prod_sub])
    await db_session.flush()

    quote = Quotation(
        quote_number="Q-HYB-1",
        customer_id=cust.id,
        sales_rep_id=rep.id,
        currency="USD",
        payment_terms_days=30,
        status=QuotationStatus.CUSTOMER_CONFIRMED.value,
        gross_subtotal=Decimal("600.00"),
        net_total=Decimal("600.00"),
        total_cost=Decimal("260.00"),
        margin_amount=Decimal("340.00"),
        margin_pct=Decimal("56.67"),
    )
    db_session.add(quote)
    await db_session.flush()

    line_onetime = QuoteLine(
        quotation_id=quote.id,
        product_id=prod_onetime.id,
        quantity=Decimal("1"),
        unit_list_price=Decimal("500.00"),
        unit_cost=Decimal("250.00"),
        gross_line_total=Decimal("500.00"),
        net_line_total=Decimal("500.00"),
        line_cost=Decimal("250.00"),
        margin_amount=Decimal("250.00"),
        margin_pct=Decimal("50.00"),
    )
    line_sub = QuoteLine(
        quotation_id=quote.id,
        product_id=prod_sub.id,
        quantity=Decimal("1"),
        unit_list_price=Decimal("100.00"),
        unit_cost=Decimal("10.00"),
        gross_line_total=Decimal("100.00"),
        net_line_total=Decimal("100.00"),
        line_cost=Decimal("10.00"),
        margin_amount=Decimal("90.00"),
        margin_pct=Decimal("90.00"),
        billing_plan_id=plan.id,
    )
    db_session.add_all([line_onetime, line_sub])
    await db_session.flush()

    v_service = QuoteVersionService(db_session)
    v1 = await v_service.create_version_snapshot(quote.id, "INITIAL_RELEASE", rep.id)
    quote.confirmed_quote_version_id = v1.id
    await db_session.commit()

    order_service = OrderService(db_session)
    order = await order_service.create_order_from_confirmed_quotation(quote.id, rep.id)

    billing_service = BillingService(db_session)
    invoices = await billing_service.initialize_order_billing(order.id, admin.id)

    assert len(invoices) >= 1
    onetime_inv = next(i for i in invoices if i.invoice_type == "ONE_TIME")
    assert onetime_inv.total_amount == Decimal("500.00")

    sub_service = SubscriptionService(db_session)
    subs = await sub_service.sub_repo.list_subscriptions(db_session, sales_order_id=order.id)
    assert len(subs) == 1
    assert subs[0].monthly_recurring_revenue == Decimal("100.00")
    assert subs[0].status == "ACTIVE"
