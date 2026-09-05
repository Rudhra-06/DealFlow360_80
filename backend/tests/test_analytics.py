"""Comprehensive Analytics Tests for Phase 6 Part 2."""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import RoleName
from app.models.user import User
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.quotation import Quotation
from app.models.sales_order import SalesOrder
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.services.analytics import AnalyticsService
from tests.conftest import get_or_create_role


@pytest.mark.asyncio
async def test_executive_overview_and_multi_currency(db_session: AsyncSession):
    role_admin = await get_or_create_role(db_session, RoleName.ADMIN)
    rep = User(email="analytics_rep@test.com", password_hash="hash", full_name="Analytics Rep", is_active=True)
    rep.roles.append(role_admin)
    db_session.add(rep)
    await db_session.flush()

    tier = CustomerTier(name="Analytics Tier")
    db_session.add(tier)
    await db_session.flush()

    cust = Customer(customer_code="CUST-ANA-01", company_name="Analytics Corp", tier_id=tier.id, assigned_sales_rep_id=rep.id)
    db_session.add(cust)
    await db_session.flush()

    # USD Quote & Order
    q_usd = Quotation(
        quotation_number="QT-USD-001",
        customer_id=cust.id,
        sales_rep_id=rep.id,
        status="CUSTOMER_CONFIRMED",
        currency="USD",
        net_total=Decimal("10000.00"),
        effective_discount_pct=Decimal("10.00"),
        margin_pct=Decimal("30.00"),
    )
    # EUR Quote & Order
    q_eur = Quotation(
        quotation_number="QT-EUR-001",
        customer_id=cust.id,
        sales_rep_id=rep.id,
        status="CUSTOMER_CONFIRMED",
        currency="EUR",
        net_total=Decimal("5000.00"),
        effective_discount_pct=Decimal("5.00"),
        margin_pct=Decimal("40.00"),
    )
    db_session.add_all([q_usd, q_eur])
    await db_session.flush()

    so_usd = SalesOrder(order_number="SO-USD-001", quotation_id=q_usd.id, customer_id=cust.id, status="FULFILLMENT", currency="USD", total_amount=Decimal("10000.00"))
    so_eur = SalesOrder(order_number="SO-EUR-001", quotation_id=q_eur.id, customer_id=cust.id, status="FULFILLMENT", currency="EUR", total_amount=Decimal("5000.00"))
    db_session.add_all([so_usd, so_eur])
    await db_session.flush()

    inv_usd = Invoice(invoice_number="INV-USD-001", customer_id=cust.id, sales_order_id=so_usd.id, status="PARTIALLY_PAID", currency="USD", subtotal=Decimal("10000.00"), tax_total=Decimal("0.00"), total_amount=Decimal("10000.00"), balance_due=Decimal("4000.00"), issue_date=datetime.now(timezone.utc), due_date=datetime.now(timezone.utc) + timedelta(days=15))
    db_session.add(inv_usd)
    await db_session.flush()

    pay_usd = Payment(payment_number="PAY-USD-001", customer_id=cust.id, invoice_id=inv_usd.id, status="COMPLETED", currency="USD", amount=Decimal("6000.00"), payment_method="CREDIT_CARD")
    db_session.add(pay_usd)
    await db_session.flush()

    sub_usd = Subscription(subscription_number="SUB-USD-001", customer_id=cust.id, status="ACTIVE", currency="USD", monthly_recurring_revenue=Decimal("500.00"), billing_frequency="MONTHLY", start_date=datetime.now(timezone.utc))
    db_session.add(sub_usd)
    await db_session.commit()

    service = AnalyticsService(db_session)
    overview = await service.get_overview()

    assert overview["quotation_count"] >= 2
    assert overview["confirmed_quote_count"] >= 2
    assert overview["order_count"] >= 2
    assert overview["confirmed_order_value"]["USD"] >= Decimal("10000.00")
    assert overview["confirmed_order_value"]["EUR"] >= Decimal("5000.00")
    assert "total" not in overview["confirmed_order_value"]  # No cross-currency sum!
    assert overview["payments_received"]["USD"] >= Decimal("6000.00")
    assert overview["monthly_recurring_revenue"]["USD"] >= Decimal("500.00")


@pytest.mark.asyncio
async def test_quotation_funnel(db_session: AsyncSession):
    service = AnalyticsService(db_session)
    funnel = await service.get_quotation_funnel()
    assert "total_quotes_created" in funnel
    assert "confirmation_rate" in funnel
    assert isinstance(funnel["stage_breakdown"], list)


@pytest.mark.asyncio
async def test_sales_performance_and_margins(db_session: AsyncSession):
    service = AnalyticsService(db_session)
    sales = await service.get_sales_performance()
    assert "reps" in sales

    margins = await service.get_margins()
    assert "overall_weighted_margin_pct" in margins
    assert "by_sales_rep" in margins


@pytest.mark.asyncio
async def test_receivables_aging(db_session: AsyncSession):
    service = AnalyticsService(db_session)
    now_utc = datetime.now(timezone.utc)
    rec = await service.get_receivables(as_of=now_utc)
    assert "buckets" in rec
    assert len(rec["buckets"]) == 5
    bucket_names = [b["bucket_name"] for b in rec["buckets"]]
    assert "CURRENT" in bucket_names
    assert "1-30 DAYS" in bucket_names
    assert "90+ DAYS" in bucket_names
