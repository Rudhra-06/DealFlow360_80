"""
DealFlow360 - deterministic 300-row mock data seeder

Purpose
-------
Adds exactly 300 mock rows to the NORMAL DealFlow360 application database
for UI / analytics / operational testing. It does NOT seed the test database
and it does NOT bypass the application's existing demo bootstrap.

Preconditions
-------------
1) Run from backend/ with the backend virtual environment active.
2) Normal app settings must point to the application DB (dealflow360), not
   dealflow360_test.
3) scripts/bootstrap_full_demo.py must already have created the demo users,
   especially salesrep.demo@example.com.
4) Run this seed once. If MOCK-* data already exists the script aborts safely.

Exactly 300 rows are inserted across:
  customer_tiers        5
  customers            40
  product_categories    5
  products              30
  warehouses             5
  inventory             40
  discount_policies      5
  approval_policies      5
  billing_plans          5
  quotations            50
  quote_lines            70
  sales_orders           15
  invoices               10
  payments                5
  subscriptions          10
                        ---
                        300

Derived workflow/audit entities such as quote versions, approval events,
negotiation messages, reservations, shipments and alerts are intentionally NOT
fabricated here. Create those through the real application workflow so existing
business rules remain authoritative.
"""

from __future__ import annotations

import asyncio
import importlib
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings


def resolve_model(class_name: str, candidates: list[str]):
    """Resolve a model without assuming one exact module filename."""
    for module_name in candidates:
        try:
            module = importlib.import_module(module_name)
            model = getattr(module, class_name, None)
            if model is not None:
                return model
        except ModuleNotFoundError:
            pass

    module = importlib.import_module("app.models")
    model = getattr(module, class_name, None)
    if model is None:
        raise ImportError(
            f"Unable to resolve model {class_name}. Checked: "
            + ", ".join(candidates + ["app.models"])
        )
    return model


User = resolve_model("User", ["app.models.user"])
CustomerTier = resolve_model("CustomerTier", ["app.models.customer_tier"])
Customer = resolve_model("Customer", ["app.models.customer"])
ProductCategory = resolve_model("ProductCategory", ["app.models.product_category"])
Product = resolve_model("Product", ["app.models.product"])
Warehouse = resolve_model("Warehouse", ["app.models.warehouse"])
Inventory = resolve_model("Inventory", ["app.models.inventory"])
DiscountPolicy = resolve_model("DiscountPolicy", ["app.models.discount_policy"])
ApprovalPolicy = resolve_model("ApprovalPolicy", ["app.models.approval_policy"])
BillingPlan = resolve_model("BillingPlan", ["app.models.billing_plan"])
Quotation = resolve_model("Quotation", ["app.models.quotation"])
QuoteLine = resolve_model("QuoteLine", ["app.models.quote_line", "app.models.quotation_line"])
SalesOrder = resolve_model("SalesOrder", ["app.models.sales_order"])
Invoice = resolve_model("Invoice", ["app.models.invoice"])
Payment = resolve_model("Payment", ["app.models.payment"])
Subscription = resolve_model("Subscription", ["app.models.subscription"])


EXPECTED_COUNTS = {
    "customer_tiers": 5,
    "customers": 40,
    "product_categories": 5,
    "products": 30,
    "warehouses": 5,
    "inventory": 40,
    "discount_policies": 5,
    "approval_policies": 5,
    "billing_plans": 5,
    "quotations": 50,
    "quote_lines": 70,
    "sales_orders": 15,
    "invoices": 10,
    "payments": 5,
    "subscriptions": 10,
}
assert sum(EXPECTED_COUNTS.values()) == 300


def D(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


async def must_not_already_be_seeded(session) -> None:
    checks = [
        (CustomerTier, CustomerTier.name, "MOCK-TIER-%"),
        (Customer, Customer.customer_code, "MOCK-CUST-%"),
        (ProductCategory, ProductCategory.name, "MOCK-CAT-%"),
        (Product, Product.sku, "MOCK-SKU-%"),
        (Warehouse, Warehouse.code, "MOCK-WH-%"),
        (Quotation, Quotation.quote_number, "MOCK-Q-%"),
        (SalesOrder, SalesOrder.order_number, "MOCK-SO-%"),
        (Invoice, Invoice.invoice_number, "MOCK-INV-%"),
        (Payment, Payment.payment_number, "MOCK-PAY-%"),
        (Subscription, Subscription.subscription_number, "MOCK-SUB-%"),
    ]
    for model, field, pattern in checks:
        count = await session.scalar(select(func.count()).select_from(model).where(field.like(pattern)))
        if count and int(count) > 0:
            raise RuntimeError(
                "MOCK data already exists. This script is intentionally non-destructive. "
                "Do not rerun it on a populated demo DB."
            )


async def main() -> None:
    url = settings.async_database_url
    if "dealflow360_test" in url.lower():
        raise RuntimeError(
            "Refusing to seed dealflow360_test. Point normal app settings to the application database."
        )

    engine = create_async_engine(url, future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        await must_not_already_be_seeded(session)

        sales_rep = await session.scalar(
            select(User).where(User.email == "salesrep.demo@example.com")
        )
        if sales_rep is None:
            raise RuntimeError(
                "salesrep.demo@example.com not found. Run scripts/bootstrap_full_demo.py first."
            )

        now = datetime.now(timezone.utc)
        inserted = 0

        # ------------------------------------------------------------------
        # 1) CUSTOMER TIERS — 5
        # ------------------------------------------------------------------
        tier_specs = [
            ("MOCK-TIER-STARTUP", "Startup / emerging accounts"),
            ("MOCK-TIER-GROWTH", "Growth-stage commercial accounts"),
            ("MOCK-TIER-ENTERPRISE", "Enterprise accounts"),
            ("MOCK-TIER-STRATEGIC", "Strategic named accounts"),
            ("MOCK-TIER-PUBLIC", "Public sector / regulated accounts"),
        ]
        tiers = [CustomerTier(name=n, description=d, is_active=True) for n, d in tier_specs]
        session.add_all(tiers)
        await session.flush()
        inserted += len(tiers)

        # ------------------------------------------------------------------
        # 2) CUSTOMERS — 40
        # ------------------------------------------------------------------
        sectors = [
            "Manufacturing", "Healthcare", "Retail", "Financial Services",
            "Technology", "Logistics", "Energy", "Telecom"
        ]
        customers = []
        for i in range(1, 41):
            tier = tiers[(i - 1) % len(tiers)]
            sector = sectors[(i - 1) % len(sectors)]
            customers.append(
                Customer(
                    customer_code=f"MOCK-CUST-{i:03d}",
                    name=f"Mock {sector} Enterprise {i:02d}",
                    email=f"procurement{i:02d}@mockcustomer.example",
                    phone=f"+1-555-01{i:02d}",
                    tier_id=tier.id,
                    billing_address=f"{100+i} Market Street, Metro City",
                    shipping_address=f"{200+i} Distribution Avenue, Metro City",
                    default_payment_terms_days=[15, 30, 30, 45, 60][(i - 1) % 5],
                    credit_limit=D(50000 + i * 10000),
                    currency="USD",
                    is_active=True,
                )
            )
        session.add_all(customers)
        await session.flush()
        inserted += len(customers)

        # ------------------------------------------------------------------
        # 3) PRODUCT CATEGORIES — 5
        # ------------------------------------------------------------------
        cat_specs = [
            ("MOCK-CAT-HARDWARE", "Enterprise compute hardware"),
            ("MOCK-CAT-NETWORK", "Networking and connectivity"),
            ("MOCK-CAT-ACCESSORIES", "Accessories and peripherals"),
            ("MOCK-CAT-SOFTWARE", "Software licenses"),
            ("MOCK-CAT-SERVICES", "Recurring services and support"),
        ]
        categories = [ProductCategory(name=n, description=d, is_active=True) for n, d in cat_specs]
        session.add_all(categories)
        await session.flush()
        inserted += len(categories)

        # ------------------------------------------------------------------
        # 4) PRODUCTS — 30
        # 1-8 Hardware, 9-14 Network, 15-20 Accessories,
        # 21-25 Software, 26-30 Services
        # ------------------------------------------------------------------
        product_names = [
            "Enterprise Laptop X1", "Enterprise Laptop X2", "Workstation Pro 15",
            "Workstation Pro 17", "Edge Server S1", "Edge Server S2",
            "Rugged Tablet R1", "Desktop Business D1",
            "Branch Router R10", "Branch Router R20", "Managed Switch 24",
            "Managed Switch 48", "WiFi Access Point AX", "Security Gateway SG",
            "USB-C Dock Standard", "USB-C Dock Pro", "27in Business Monitor",
            "34in Ultrawide Monitor", "Wireless Keyboard", "Business Headset",
            "Analytics Suite Basic", "Analytics Suite Pro", "CRM Connector",
            "Data Protection License", "Workflow Automation License",
            "24x7 Standard Support", "24x7 Premium Support", "Managed Device Care",
            "Remote Admin Service", "Success Management Plan",
        ]
        products = []
        for i, name in enumerate(product_names, start=1):
            if i <= 8:
                cat = categories[0]
            elif i <= 14:
                cat = categories[1]
            elif i <= 20:
                cat = categories[2]
            elif i <= 25:
                cat = categories[3]
            else:
                cat = categories[4]

            list_price = D(100 + i * 85)
            cost_ratio = Decimal("0.58") if i <= 20 else Decimal("0.25")
            products.append(
                Product(
                    sku=f"MOCK-SKU-{i:03d}",
                    name=name,
                    description=f"Mock catalog item for {name}",
                    category_id=cat.id,
                    list_price=list_price,
                    cost_price=(list_price * cost_ratio).quantize(Decimal("0.01")),
                    currency="USD",
                    unit_of_measure="EA",
                    is_active=True,
                )
            )
        session.add_all(products)
        await session.flush()
        inserted += len(products)

        # ------------------------------------------------------------------
        # 5) WAREHOUSES — 5
        # ------------------------------------------------------------------
        warehouse_specs = [
            ("MOCK-WH-EAST", "Mock East DC", "East Region", 1, 18),
            ("MOCK-WH-CENTRAL", "Mock Central DC", "Central Region", 2, 15),
            ("MOCK-WH-WEST", "Mock West DC", "West Region", 3, 22),
            ("MOCK-WH-SOUTH", "Mock South DC", "South Region", 4, 20),
            ("MOCK-WH-NORTH", "Mock North DC", "North Region", 5, 24),
        ]
        warehouses = []
        for code, name, location, priority, ship_cost in warehouse_specs:
            warehouses.append(
                Warehouse(
                    code=code,
                    name=name,
                    location=location,
                    address=f"{priority}00 Logistics Park, {location}",
                    fulfillment_priority=priority,
                    shipping_cost_weight=Decimal("1.00"),
                    base_shipping_cost=D(ship_cost),
                    is_active=True,
                )
            )
        session.add_all(warehouses)
        await session.flush()
        inserted += len(warehouses)

        # ------------------------------------------------------------------
        # 6) INVENTORY — 40
        # 5 warehouses x first 8 physical products
        # ------------------------------------------------------------------
        inventory_rows = []
        for w_idx, wh in enumerate(warehouses, start=1):
            for p_idx, product in enumerate(products[:8], start=1):
                on_hand = Decimal(str(8 + ((w_idx * 7 + p_idx * 3) % 35)))
                reserved = Decimal(str((w_idx + p_idx) % 4))
                inventory_rows.append(
                    Inventory(
                        warehouse_id=wh.id,
                        product_id=product.id,
                        on_hand_qty=on_hand,
                        reserved_qty=reserved,
                        reorder_level=Decimal("5"),
                    )
                )
        session.add_all(inventory_rows)
        await session.flush()
        inserted += len(inventory_rows)

        # ------------------------------------------------------------------
        # 7) DISCOUNT POLICIES — 5
        # Unique scope/priority combinations avoid ambiguity with DEMO-DISC-01.
        # ------------------------------------------------------------------
        discount_policies = [
            DiscountPolicy(
                name="MOCK-DISC-STARTUP",
                customer_tier_id=tiers[0].id,
                standard_discount_pct=D(3), max_discount_pct=D(8),
                priority=201, effective_from=now - timedelta(days=1), is_active=True,
            ),
            DiscountPolicy(
                name="MOCK-DISC-GROWTH",
                customer_tier_id=tiers[1].id,
                standard_discount_pct=D(5), max_discount_pct=D(12),
                priority=202, effective_from=now - timedelta(days=1), is_active=True,
            ),
            DiscountPolicy(
                name="MOCK-DISC-ENTERPRISE",
                customer_tier_id=tiers[2].id,
                standard_discount_pct=D(7), max_discount_pct=D(15),
                priority=203, effective_from=now - timedelta(days=1), is_active=True,
            ),
            DiscountPolicy(
                name="MOCK-DISC-HARDWARE",
                product_category_id=categories[0].id,
                standard_discount_pct=D(4), max_discount_pct=D(10),
                priority=204, effective_from=now - timedelta(days=1), is_active=True,
            ),
            DiscountPolicy(
                name="MOCK-DISC-SUPPORT",
                product_category_id=categories[4].id,
                standard_discount_pct=D(8), max_discount_pct=D(18),
                priority=205, effective_from=now - timedelta(days=1), is_active=True,
            ),
        ]
        session.add_all(discount_policies)
        await session.flush()
        inserted += len(discount_policies)

        # ------------------------------------------------------------------
        # 8) APPROVAL POLICIES — 5
        # One tier-scoped policy each keeps rules deterministic.
        # ------------------------------------------------------------------
        approval_policies = [
            ApprovalPolicy(
                name="MOCK-APP-STARTUP-DISCOUNT", customer_tier_id=tiers[0].id,
                discount_above_pct=D(8), approval_role="SALES_MANAGER",
                priority=201, is_active=True,
            ),
            ApprovalPolicy(
                name="MOCK-APP-GROWTH-DISCOUNT", customer_tier_id=tiers[1].id,
                discount_above_pct=D(12), approval_role="SALES_MANAGER",
                priority=202, is_active=True,
            ),
            ApprovalPolicy(
                name="MOCK-APP-ENTERPRISE-MARGIN", customer_tier_id=tiers[2].id,
                margin_below_pct=D(22), approval_role="SALES_MANAGER",
                priority=203, is_active=True,
            ),
            ApprovalPolicy(
                name="MOCK-APP-STRATEGIC-TERMS", customer_tier_id=tiers[3].id,
                payment_terms_above_days=45, approval_role="FINANCE_OPERATIONS",
                priority=204, is_active=True,
            ),
            ApprovalPolicy(
                name="MOCK-APP-PUBLIC-RISK", customer_tier_id=tiers[4].id,
                blended_risk_above=D(60), approval_role="FINANCE_OPERATIONS",
                priority=205, is_active=True,
            ),
        ]
        session.add_all(approval_policies)
        await session.flush()
        inserted += len(approval_policies)

        # ------------------------------------------------------------------
        # 9) BILLING PLANS — 5
        # ------------------------------------------------------------------
        billing_plans = [
            BillingPlan(
                code="MOCK-BP-MONTHLY", name="Mock Monthly Recurring",
                billing_type="RECURRING", billing_interval_months=1,
                payment_due_days=30, proration_method="DAILY",
                cancellation_method="END_OF_PERIOD", is_active=True,
            ),
            BillingPlan(
                code="MOCK-BP-QUARTERLY", name="Mock Quarterly Recurring",
                billing_type="RECURRING", billing_interval_months=3,
                payment_due_days=30, proration_method="DAILY",
                cancellation_method="END_OF_PERIOD", is_active=True,
            ),
            BillingPlan(
                code="MOCK-BP-SEMIANNUAL", name="Mock Semiannual Recurring",
                billing_type="RECURRING", billing_interval_months=6,
                payment_due_days=30, proration_method="DAILY",
                cancellation_method="END_OF_PERIOD", is_active=True,
            ),
            BillingPlan(
                code="MOCK-BP-ANNUAL", name="Mock Annual Recurring",
                billing_type="RECURRING", billing_interval_months=12,
                payment_due_days=30, proration_method="DAILY",
                cancellation_method="END_OF_PERIOD", is_active=True,
            ),
            BillingPlan(
                code="MOCK-BP-ONETIME", name="Mock One-Time",
                billing_type="ONE_TIME", billing_interval_months=None,
                payment_due_days=30, proration_method="DAILY",
                cancellation_method="END_OF_PERIOD", is_active=True,
            ),
        ]
        session.add_all(billing_plans)
        await session.flush()
        inserted += len(billing_plans)

        # ------------------------------------------------------------------
        # 10) QUOTATIONS — 50
        # Safe historic/list/analytics records. Workflow-derived entities are
        # not fabricated; use the real UI workflow for approval/negotiation.
        # ------------------------------------------------------------------
        quotations = []
        quote_meta: dict[int, dict[str, Decimal]] = {}
        for i in range(1, 51):
            if i <= 15:
                status = "DRAFT"
            elif i <= 25:
                status = "APPROVED"
            elif i <= 35:
                status = "SENT_TO_CUSTOMER"
            else:
                status = "CUSTOMER_CONFIRMED"

            gross = D(1200 + i * 175)
            discount_pct = D([3, 5, 7, 10, 12, 15][(i - 1) % 6])
            discount_amount = (gross * discount_pct / Decimal("100")).quantize(Decimal("0.01"))
            net = (gross - discount_amount).quantize(Decimal("0.01"))
            total_cost = (gross * Decimal("0.58")).quantize(Decimal("0.01"))
            margin_amount = (net - total_cost).quantize(Decimal("0.01"))
            margin_pct = (
                (margin_amount / net * Decimal("100")).quantize(Decimal("0.01"))
                if net else Decimal("0.00")
            )
            risk_score = D(20 + ((i - 1) % 5) * 15)
            if risk_score < Decimal("35"):
                risk_level = "GREEN"
            elif risk_score < Decimal("55"):
                risk_level = "WATCH"
            elif risk_score < Decimal("75"):
                risk_level = "AT_RISK"
            else:
                risk_level = "CRITICAL"

            q = Quotation(
                quote_number=f"MOCK-Q-{i:04d}",
                customer_id=customers[(i - 1) % len(customers)].id,
                sales_rep_id=sales_rep.id,
                status=status,
                currency="USD",
                payment_terms_days=[15, 30, 30, 45, 60][(i - 1) % 5],
                order_discount_pct=discount_pct,
                gross_subtotal=gross,
                discount_amount=discount_amount,
                net_total=net,
                total_cost=total_cost,
                margin_amount=margin_amount,
                margin_pct=margin_pct,
                weighted_effective_discount_pct=discount_pct,
                blended_risk_score=risk_score,
                risk_level=risk_level,
                submitted_at=(now - timedelta(days=(51 - i))) if status != "DRAFT" else None,
            )
            quotations.append(q)
            quote_meta[i] = {
                "gross": gross,
                "discount_pct": discount_pct,
                "discount_amount": discount_amount,
                "net": net,
                "total_cost": total_cost,
                "margin_amount": margin_amount,
                "margin_pct": margin_pct,
            }

        session.add_all(quotations)
        await session.flush()
        inserted += len(quotations)

        # ------------------------------------------------------------------
        # 11) QUOTE LINES — 70
        # Every quote gets one physical line. Quotes 31-50 get a second
        # recurring service line, giving useful hybrid-billing examples.
        # ------------------------------------------------------------------
        quote_lines = []
        for i, quote in enumerate(quotations, start=1):
            meta = quote_meta[i]
            has_second = i >= 31
            physical_share = Decimal("0.70") if has_second else Decimal("1.00")

            gross1 = (meta["gross"] * physical_share).quantize(Decimal("0.01"))
            disc1 = (gross1 * meta["discount_pct"] / Decimal("100")).quantize(Decimal("0.01"))
            net1 = (gross1 - disc1).quantize(Decimal("0.01"))
            cost1 = (gross1 * Decimal("0.58")).quantize(Decimal("0.01"))
            margin1 = (net1 - cost1).quantize(Decimal("0.01"))
            margin_pct1 = (margin1 / net1 * Decimal("100")).quantize(Decimal("0.01")) if net1 else D(0)
            product1 = products[(i - 1) % 8]

            quote_lines.append(
                QuoteLine(
                    quotation_id=quote.id,
                    product_id=product1.id,
                    quantity=Decimal("1"),
                    unit_list_price=gross1,
                    unit_cost=cost1,
                    line_discount_pct=meta["discount_pct"],
                    effective_discount_pct=meta["discount_pct"],
                    gross_line_total=gross1,
                    discount_amount=disc1,
                    net_line_total=net1,
                    line_cost=cost1,
                    margin_amount=margin1,
                    margin_pct=margin_pct1,
                    risk_level=quote.risk_level,
                )
            )

            if has_second:
                gross2 = (meta["gross"] * Decimal("0.30")).quantize(Decimal("0.01"))
                disc2 = (gross2 * meta["discount_pct"] / Decimal("100")).quantize(Decimal("0.01"))
                net2 = (gross2 - disc2).quantize(Decimal("0.01"))
                cost2 = (gross2 * Decimal("0.58")).quantize(Decimal("0.01"))
                margin2 = (net2 - cost2).quantize(Decimal("0.01"))
                margin_pct2 = (margin2 / net2 * Decimal("100")).quantize(Decimal("0.01")) if net2 else D(0)
                service_product = products[25 + ((i - 31) % 5)]

                quote_lines.append(
                    QuoteLine(
                        quotation_id=quote.id,
                        product_id=service_product.id,
                        quantity=Decimal("1"),
                        unit_list_price=gross2,
                        unit_cost=cost2,
                        line_discount_pct=meta["discount_pct"],
                        effective_discount_pct=meta["discount_pct"],
                        gross_line_total=gross2,
                        discount_amount=disc2,
                        net_line_total=net2,
                        line_cost=cost2,
                        margin_amount=margin2,
                        margin_pct=margin_pct2,
                        risk_level=quote.risk_level,
                        billing_plan_id=billing_plans[0].id,
                    )
                )

        assert len(quote_lines) == 70
        session.add_all(quote_lines)
        await session.flush()
        inserted += len(quote_lines)

        # ------------------------------------------------------------------
        # 12) SALES ORDERS — 15
        # Tied 1:1 to the 15 CUSTOMER_CONFIRMED quotes (36-50).
        # ------------------------------------------------------------------
        confirmed_quotes = quotations[35:50]
        sales_orders = []
        for i, quote in enumerate(confirmed_quotes, start=1):
            status = "FULFILLMENT" if i <= 8 else ("BACKORDERED" if i <= 11 else "COMPLETED")
            sales_orders.append(
                SalesOrder(
                    order_number=f"MOCK-SO-{i:03d}",
                    quotation_id=quote.id,
                    customer_id=quote.customer_id,
                    status=status,
                    currency=quote.currency,
                    total_amount=quote.net_total,
                )
            )
        session.add_all(sales_orders)
        await session.flush()
        inserted += len(sales_orders)

        # ------------------------------------------------------------------
        # 13) INVOICES — 10
        # ------------------------------------------------------------------
        invoices = []
        for i, order in enumerate(sales_orders[:10], start=1):
            total = D(1800 + i * 525)
            if i <= 4:
                status = "UNPAID"
                balance = total
            elif i <= 7:
                status = "PARTIALLY_PAID"
                balance = (total * Decimal("0.50")).quantize(Decimal("0.01"))
            else:
                status = "PAID"
                balance = Decimal("0.00")

            issue = now - timedelta(days=20 - i)
            invoices.append(
                Invoice(
                    invoice_number=f"MOCK-INV-{i:03d}",
                    customer_id=order.customer_id,
                    sales_order_id=order.id,
                    status=status,
                    currency="USD",
                    subtotal=total,
                    tax_total=Decimal("0.00"),
                    total_amount=total,
                    balance_due=balance,
                    issue_date=issue,
                    due_date=issue + timedelta(days=30),
                )
            )
        session.add_all(invoices)
        await session.flush()
        inserted += len(invoices)

        # ------------------------------------------------------------------
        # 14) PAYMENTS — 5
        # Invoice 5-7 partial, 8-9 paid.
        # ------------------------------------------------------------------
        payments = []
        for seq, invoice in enumerate(invoices[4:9], start=1):
            paid_amount = (invoice.total_amount - invoice.balance_due).quantize(Decimal("0.01"))
            if paid_amount <= 0:
                paid_amount = (invoice.total_amount * Decimal("0.25")).quantize(Decimal("0.01"))
            payments.append(
                Payment(
                    payment_number=f"MOCK-PAY-{seq:03d}",
                    customer_id=invoice.customer_id,
                    invoice_id=invoice.id,
                    status="COMPLETED",
                    currency="USD",
                    amount=paid_amount,
                    payment_method=["WIRE_TRANSFER", "CREDIT_CARD", "ACH", "WIRE_TRANSFER", "ACH"][seq - 1],
                )
            )
        session.add_all(payments)
        await session.flush()
        inserted += len(payments)

        # ------------------------------------------------------------------
        # 15) SUBSCRIPTIONS — 10
        # ------------------------------------------------------------------
        subscriptions = []
        for i, order in enumerate(sales_orders[:10], start=1):
            start = now - timedelta(days=90 - i * 3)
            unit_price = D(149 + i * 25)
            plan = billing_plans[(i - 1) % 4]
            interval = int(plan.billing_interval_months or 1)
            subscriptions.append(
                Subscription(
                    subscription_number=f"MOCK-SUB-{i:03d}",
                    sales_order_id=order.id,
                    sales_order_line_id=None,
                    customer_id=order.customer_id,
                    billing_plan_id=plan.id,
                    status="ACTIVE" if i <= 8 else "CANCELLED",
                    quantity=Decimal("1"),
                    unit_price=unit_price,
                    currency="USD",
                    interval_months=interval,
                    proration_method="DAILY",
                    cancellation_method="END_OF_PERIOD",
                    start_date=start,
                    current_period_start=start,
                    current_period_end=start + timedelta(days=30 * interval),
                    next_billing_date=(start + timedelta(days=30 * interval)) if i <= 8 else None,
                    cancelled_at=(now - timedelta(days=i)) if i > 8 else None,
                    ended_at=None,
                )
            )
        session.add_all(subscriptions)
        await session.flush()
        inserted += len(subscriptions)

        if inserted != 300:
            raise RuntimeError(f"Internal seed count error: expected 300, prepared {inserted}")

        await session.commit()

        print("=" * 68)
        print("DEALFLOW360 — 300 MOCK RECORDS INSERTED SUCCESSFULLY")
        print("=" * 68)
        for table_name, count in EXPECTED_COUNTS.items():
            print(f"{table_name:24s} {count:3d}")
        print("-" * 68)
        print(f"TOTAL                    {inserted:3d}")
        print("Database URL uses normal application settings.")
        print("No workflow-derived approval/negotiation/shipment/audit records were faked.")
        print("=" * 68)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
