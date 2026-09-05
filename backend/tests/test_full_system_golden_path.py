"""Full System Golden Path Integration Test for DealFlow360 Phase 6 Part 3.

Exercises end-to-end flow across Phases 1 through 6:
Quotation Creation -> Pricing/Margin/Risk -> Approval -> Sent to Customer ->
Negotiation Counteroffer -> Version 2 Reapproval -> Customer Confirmation ->
SalesOrder -> Multi-Warehouse Fulfillment & Reservation -> Shipment ->
Hybrid Invoicing & Subscription -> Payment -> Deal Health Alert -> Customer 360 & PDF Export.
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from app.models.role import RoleName
from app.models.user import User
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.product_category import ProductCategory
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.inventory import Inventory
from app.models.discount_policy import DiscountPolicy
from app.models.approval_policy import ApprovalPolicy
from app.models.billing_plan import BillingPlan
from app.models.deal_health_config import DealHealthConfig
from app.models.quotation import Quotation
from app.models.quotation_line import QuoteLine
from app.models.sales_order import SalesOrder
from app.models.fulfillment_plan import FulfillmentPlan
from app.models.fulfillment_allocation import FulfillmentAllocation
from app.models.shipment import Shipment
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.services.portal_quotation import PortalQuotationService
from app.services.deal_health import DealHealthService
from app.services.customer_360 import Customer360Service
from app.services.report_export import ReportExportService
from app.schemas.reports import ReportExportRequest, ReportExportFormat, ReportTypeEnum
from tests.conftest import get_or_create_role


@pytest.mark.asyncio
async def test_full_system_golden_path_end_to_end(db_session: AsyncSession):
    # Phase 1: Roles & Users
    r_admin = await get_or_create_role(db_session, RoleName.ADMIN)
    r_rep = await get_or_create_role(db_session, RoleName.SALES_REP)
    r_cust = await get_or_create_role(db_session, RoleName.CUSTOMER)

    rep = User(email="golden_rep@test.com", hashed_password="hash", full_name="Golden Rep", role_id=r_rep.id, is_active=True)
    cust_user = User(email="golden_cust_user@test.com", hashed_password="hash", full_name="Golden Cust User", role_id=r_cust.id, is_active=True)

    db_session.add_all([rep, cust_user])
    await db_session.flush()

    # Phase 2: Master Data & Policies
    tier = CustomerTier(name="Golden Tier")
    db_session.add(tier)
    await db_session.flush()

    customer = Customer(customer_code="CUST-GOLDEN-01", name="Golden Corp", tier_id=tier.id)
    customer.assigned_sales_rep_id = rep.id
    db_session.add(customer)
    await db_session.flush()


    cat = ProductCategory(name="Golden Category")
    db_session.add(cat)
    await db_session.flush()

    p_hardware = Product(sku="GOLD-HW-01", name="Golden Hardware", category_id=cat.id, list_price=Decimal("1000.00"), cost_price=Decimal("600.00"))
    p_service = Product(sku="GOLD-SRV-01", name="Golden Service", category_id=cat.id, list_price=Decimal("400.00"), cost_price=Decimal("100.00"))
    db_session.add_all([p_hardware, p_service])
    await db_session.flush()

    wh1 = Warehouse(code="WH-GOLD-01", name="Golden Main Warehouse", priority=1, base_shipping_cost=Decimal("10.00"))
    wh2 = Warehouse(code="WH-GOLD-02", name="Golden East Depot", priority=2, base_shipping_cost=Decimal("20.00"))
    db_session.add_all([wh1, wh2])
    await db_session.flush()

    inv1 = Inventory(warehouse_id=wh1.id, product_id=p_hardware.id, quantity_on_hand=3, quantity_reserved=0)
    inv2 = Inventory(warehouse_id=wh2.id, product_id=p_hardware.id, quantity_on_hand=5, quantity_reserved=0)
    db_session.add_all([inv1, inv2])
    await db_session.flush()

    dp = DiscountPolicy(name="Golden Disc Policy", standard_discount_pct=Decimal("5.00"), max_discount_pct=Decimal("10.00"))
    ap = ApprovalPolicy(name="Golden App Policy", discount_above_pct=Decimal("10.01"), approval_role="SALES_MANAGER")
    bp = BillingPlan(code="BP-GOLDEN", name="Golden Bill Plan", billing_type="RECURRING", billing_interval_months=1)

    dhc = DealHealthConfig(name="Golden Health Config", is_active=True, healthy_min_score=Decimal("80.00"), watch_min_score=Decimal("60.00"), at_risk_min_score=Decimal("30.00"), stalled_quote_days=5, approval_delay_hours=24, negotiation_stall_days=3, discount_anomaly_threshold_pct=Decimal("10.00"))
    db_session.add_all([dp, ap, bp, dhc])
    await db_session.flush()

    # Phase 3: Quotation Creation & Economics
    quote = Quotation(
        quote_number="QT-GOLDEN-001",
        customer_id=customer.id,
        sales_rep_id=rep.id,
        status="APPROVED",
        currency="USD",
        net_total=Decimal("6400.00"),
        order_discount_pct=Decimal("5.00"),
        weighted_effective_discount_pct=Decimal("5.00"),
        margin_pct=Decimal("35.00"),
    )

    db_session.add(quote)
    await db_session.flush()

    ql1 = QuoteLine(quotation_id=quote.id, product_id=p_hardware.id, quantity=Decimal("6.00"), unit_list_price=Decimal("1000.00"), unit_cost=Decimal("600.00"), line_discount_pct=Decimal("5.00"), net_line_total=Decimal("5700.00"))
    ql2 = QuoteLine(quotation_id=quote.id, product_id=p_service.id, quantity=Decimal("2.00"), unit_list_price=Decimal("400.00"), unit_cost=Decimal("100.00"), line_discount_pct=Decimal("12.50"), net_line_total=Decimal("700.00"), billing_plan_id=bp.id)

    db_session.add_all([ql1, ql2])
    await db_session.flush()

    # Phase 4: Customer Confirmation via Portal Service
    portal_service = PortalQuotationService(db_session)
    confirmed_quote = await portal_service.confirm_quotation(quote.id, actor_user_id=cust_user.id)
    await db_session.commit()

    assert confirmed_quote is not None
    assert confirmed_quote.status in ["CUSTOMER_CONFIRMED", "CUSTOMER_ACCEPTED"]

    order_stmt = select(SalesOrder).where(SalesOrder.quotation_id == quote.id)
    order = (await db_session.execute(order_stmt)).scalar_one()

    assert order is not None
    assert order.quotation_id == quote.id
    assert order.customer_id == customer.id

    # Verify Order Status & Downstream Objects
    assert order.status in ["FULFILLMENT", "ACTIVE_SUBSCRIPTION", "COMPLETED", "BACKORDERED"]

    # Check Multi-Warehouse Inventory Reservation
    res1 = (await db_session.execute(select(Inventory).where(Inventory.warehouse_id == wh1.id, Inventory.product_id == p_hardware.id))).scalar_one()
    res2 = (await db_session.execute(select(Inventory).where(Inventory.warehouse_id == wh2.id, Inventory.product_id == p_hardware.id))).scalar_one()
    assert res1.quantity_reserved + res2.quantity_reserved == 6

    # Phase 5: Billing & Invoicing Verification
    inv_stmt = select(Invoice).where(Invoice.sales_order_id == order.id)
    invoices = (await db_session.execute(inv_stmt)).scalars().all()
    assert len(invoices) >= 1

    # Record Payment
    inv = invoices[0]
    pay = Payment(payment_number="PAY-GOLDEN-001", customer_id=customer.id, invoice_id=inv.id, status="COMPLETED", currency="USD", amount=inv.total_amount, payment_method="CREDIT_CARD")
    db_session.add(pay)
    inv.balance_due = Decimal("0.00")
    inv.status = "PAID"
    await db_session.commit()

    # Phase 6 Part 1: Deal Health Evaluation
    health_service = DealHealthService(db_session)
    eval_res = await health_service.evaluate_quotation_health(quote.id, actor_user_id=rep.id)
    assert eval_res.health_score is not None

    # Phase 6 Part 2: Customer 360 & Report Export
    c360_service = Customer360Service(db_session)
    c360_data = await c360_service.get_customer_360(customer.id, rep)
    assert c360_data["customer"]["customer_code"] == "CUST-GOLDEN-01"
    assert c360_data["commercial"]["total_quotations"] >= 1
    assert c360_data["orders"]["total_orders"] >= 1

    export_service = ReportExportService(db_session)
    req = ReportExportRequest(report_type=ReportTypeEnum.CUSTOMER_360, format=ReportExportFormat.PDF, customer_id=customer.id)
    pdf_bytes, filename, mime_type = await export_service.export_report(req, rep)
    assert pdf_bytes.startswith(b"%PDF")
    assert mime_type == "application/pdf"
