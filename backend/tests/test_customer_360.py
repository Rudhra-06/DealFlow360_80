"""Customer 360 Tests for Phase 6 Part 2."""

pytest_plugins = ('pytest_asyncio',)

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import RoleName
from app.models.user import User
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.quotation import Quotation
from app.models.sales_order import SalesOrder
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.billing_plan import BillingPlan
from app.services.customer_360 import Customer360Service
from tests.conftest import get_or_create_role


@pytest.mark.asyncio
async def test_customer_360_full_aggregation(db_session: AsyncSession):
    role_admin = await get_or_create_role(db_session, RoleName.ADMIN)
    rep = User(email="c360_rep@test.com", hashed_password="hash", full_name="C360 Rep", role_id=role_admin.id, is_active=True)
    db_session.add(rep)
    await db_session.flush()

    tier = CustomerTier(name="Gold Tier 360")
    db_session.add(tier)
    await db_session.flush()

    cust = Customer(customer_code="CUST-360-01", name="Omega 360 Corp", tier_id=tier.id)
    cust.assigned_sales_rep_id = rep.id
    db_session.add(cust)
    await db_session.flush()

    q = Quotation(
        quote_number="QT-360-001",
        customer_id=cust.id,
        sales_rep_id=rep.id,
        status="CUSTOMER_CONFIRMED",
        currency="USD",
        net_total=Decimal("25000.00"),
        order_discount_pct=Decimal("12.00"),
        weighted_effective_discount_pct=Decimal("12.00"),
        margin_pct=Decimal("35.00"),
    )
    db_session.add(q)
    await db_session.flush()

    so = SalesOrder(order_number="SO-360-001", quotation_id=q.id, customer_id=cust.id, status="FULFILLMENT", currency="USD", total_amount=Decimal("25000.00"))
    db_session.add(so)
    await db_session.flush()

    inv = Invoice(invoice_number="INV-360-001", customer_id=cust.id, sales_order_id=so.id, status="PARTIALLY_PAID", currency="USD", subtotal=Decimal("25000.00"), tax_total=Decimal("0.00"), total_amount=Decimal("25000.00"), balance_due=Decimal("10000.00"), issue_date=datetime.now(timezone.utc), due_date=datetime.now(timezone.utc) + timedelta(days=30))
    db_session.add(inv)
    await db_session.flush()

    pay = Payment(payment_number="PAY-360-001", customer_id=cust.id, invoice_id=inv.id, status="COMPLETED", currency="USD", amount=Decimal("15000.00"), payment_method="WIRE_TRANSFER")
    db_session.add(pay)
    await db_session.flush()

    plan = BillingPlan(
        code="BP-C360-MONTHLY",
        name="Customer360 Monthly",
        billing_type="RECURRING",
        billing_interval_months=1,
        proration_method="DAILY",
        cancellation_method="END_OF_PERIOD",
        is_active=True,
    )
    db_session.add(plan)
    await db_session.flush()

    sub = Subscription(subscription_number="SUB-360-001", customer_id=cust.id, sales_order_id=so.id, billing_plan_id=plan.id, status="ACTIVE", currency="USD", monthly_recurring_revenue=Decimal("1500.00"), billing_frequency="MONTHLY", start_date=datetime.now(timezone.utc))
    db_session.add(sub)
    await db_session.commit()

    service = Customer360Service(db_session)
    res = await service.get_customer_360(cust.id, rep)

    assert res["customer"]["customer_code"] == "CUST-360-01"
    assert res["commercial"]["total_quotations"] >= 1
    assert res["commercial"]["confirmed_quotations"] >= 1
    assert res["orders"]["total_orders"] >= 1
    assert res["billing"]["invoice_count"] >= 1
    assert res["billing"]["outstanding_balance_by_currency"]["USD"] == Decimal("10000.00")
    assert res["subscriptions"]["active_subscriptions"] >= 1
    assert res["subscriptions"]["monthly_recurring_revenue"]["USD"] == Decimal("1500.00")
    assert isinstance(res["recent_activity"], list)
    assert len(res["recent_activity"]) >= 1


@pytest.mark.asyncio
async def test_customer_360_security_isolation(db_session: AsyncSession):
    role_rep = await get_or_create_role(db_session, RoleName.SALES_REP)
    rep1 = User(email="rep1_360@test.com", hashed_password="hash", full_name="Rep One", role_id=role_rep.id, is_active=True)
    rep2 = User(email="rep2_360@test.com", hashed_password="hash", full_name="Rep Two", role_id=role_rep.id, is_active=True)

    db_session.add_all([rep1, rep2])
    await db_session.flush()

    tier = CustomerTier(name="Tier 360 Security")
    db_session.add(tier)
    await db_session.flush()

    cust1 = Customer(customer_code="CUST-360-REP1", name="Rep1 Customer", tier_id=tier.id)
    cust1.assigned_sales_rep_id = rep1.id
    db_session.add(cust1)
    await db_session.commit()


    service = Customer360Service(db_session)

    # Rep 1 can access own customer
    res = await service.get_customer_360(cust1.id, rep1)
    assert res["customer"]["customer_id"] == cust1.id

    # Rep 2 trying to access Rep 1 customer yields 403
    with pytest.raises(HTTPException) as exc_info:
        await service.get_customer_360(cust1.id, rep2)
    assert exc_info.value.status_code == 403
