"""Full Demo Data Bootstrap Script for DealFlow360 Phase 6 Part 3.

Idempotent seed script that sets up reviewer demo users, master data,
warehouses, inventory, commercial policies, deal health configs, and
golden demo start state.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal

# Ensure backend path in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.core.security import hash_password as get_password_hash
from app.models.role import Role, RoleName
from app.models.user import User
from app.models.customer_tier import CustomerTier
from app.models.customer import Customer
from app.models.customer_portal_access import CustomerPortalAccess
from app.models.product_category import ProductCategory
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.inventory import Inventory
from app.models.discount_policy import DiscountPolicy
from app.models.approval_policy import ApprovalPolicy
from app.models.billing_plan import BillingPlan
from app.models.deal_health_config import DealHealthConfig
from app.models.quotation import Quotation


DEMO_PASSWORD = os.getenv("DEMO_USER_PASSWORD", "DealFlow360Demo123!")


async def get_or_create_role(session: AsyncSession, name: RoleName) -> Role:
    role_str = name.value if isinstance(name, RoleName) else str(name)
    stmt = select(Role).where(Role.name == role_str)
    res = await session.execute(stmt)
    role = res.scalar_one_or_none()
    if not role:
        role = Role(name=role_str, description=f"{role_str} role")
        session.add(role)
        await session.flush()
    return role


async def get_or_create_user(session: AsyncSession, email: str, full_name: str, role: Role) -> User:
    stmt = select(User).where(User.email == email)
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()
    pwd_hash = get_password_hash(DEMO_PASSWORD)
    if not user:
        user = User(
            email=email,
            hashed_password=pwd_hash,
            full_name=full_name,
            role_id=role.id,
            is_active=True,
        )
        session.add(user)
        await session.flush()
    else:
        user.hashed_password = pwd_hash
        user.full_name = full_name
        user.role_id = role.id
        user.is_active = True
        await session.flush()
    return user


async def bootstrap_demo():
    print("Starting DealFlow360 Demo Data Bootstrap...")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # 1. Roles
            r_admin = await get_or_create_role(session, RoleName.ADMIN)
            r_mgr = await get_or_create_role(session, RoleName.SALES_MANAGER)
            r_fin = await get_or_create_role(session, RoleName.FINANCE_OPERATIONS)
            r_rep = await get_or_create_role(session, RoleName.SALES_REP)
            r_cust = await get_or_create_role(session, RoleName.CUSTOMER)

            # 2. Users
            u_admin = await get_or_create_user(session, "admin.demo@example.com", "Demo Admin User", r_admin)
            u_mgr = await get_or_create_user(session, "manager.demo@example.com", "Demo Sales Manager", r_mgr)
            u_fin = await get_or_create_user(session, "finance.demo@example.com", "Demo Finance User", r_fin)
            u_rep = await get_or_create_user(session, "salesrep.demo@example.com", "Demo Sales Rep", r_rep)
            u_cust = await get_or_create_user(session, "customer.demo@example.com", "Demo Customer Contact", r_cust)

            # 3. Customer Tier & Customer
            t_stmt = select(CustomerTier).where(CustomerTier.name == "Gold Enterprise")
            tier = (await session.execute(t_stmt)).scalar_one_or_none()
            if not tier:
                tier = CustomerTier(name="Gold Enterprise", description="Gold Enterprise Tier", is_active=True)
                session.add(tier)
                await session.flush()

            c_stmt = select(Customer).where(Customer.customer_code == "DEMO-CUST-OMEGA")
            customer = (await session.execute(c_stmt)).scalar_one_or_none()
            if not customer:
                customer = Customer(
                    customer_code="DEMO-CUST-OMEGA",
                    name="Omega Corporation",
                    email="customer.demo@example.com",
                    tier_id=tier.id,
                    is_active=True,
                )
                session.add(customer)
                await session.flush()
            else:
                customer.name = "Omega Corporation"
                customer.email = "customer.demo@example.com"
                customer.tier_id = tier.id
                customer.is_active = True
                await session.flush()

            # Customer Portal Access association
            cpa_stmt = select(CustomerPortalAccess).where(CustomerPortalAccess.user_id == u_cust.id)
            cpa = (await session.execute(cpa_stmt)).scalar_one_or_none()
            if not cpa:
                cpa = CustomerPortalAccess(
                    user_id=u_cust.id,
                    customer_id=customer.id,
                    is_active=True,
                )
                session.add(cpa)
                await session.flush()
            else:
                cpa.customer_id = customer.id
                cpa.is_active = True
                await session.flush()

            # 4. Categories & Products
            cat_hw = (await session.execute(select(ProductCategory).where(ProductCategory.name == "Hardware"))).scalar_one_or_none()
            if not cat_hw:
                cat_hw = ProductCategory(name="Hardware", description="Enterprise Hardware", is_active=True)
                session.add(cat_hw)
                await session.flush()

            cat_srv = (await session.execute(select(ProductCategory).where(ProductCategory.name == "Services"))).scalar_one_or_none()
            if not cat_srv:
                cat_srv = ProductCategory(name="Services", description="Professional Services & Support", is_active=True)
                session.add(cat_srv)
                await session.flush()

            p_laptop = (await session.execute(select(Product).where(Product.sku == "DEMO-LAPTOP"))).scalar_one_or_none()
            if not p_laptop:
                p_laptop = Product(
                    sku="DEMO-LAPTOP",
                    name="Enterprise Laptop Pro",
                    category_id=cat_hw.id,
                    list_price=Decimal("1500.00"),
                    cost_price=Decimal("900.00"),
                    is_active=True,
                )
                session.add(p_laptop)
                await session.flush()

            p_dock = (await session.execute(select(Product).where(Product.sku == "DEMO-DOCK"))).scalar_one_or_none()
            if not p_dock:
                p_dock = Product(
                    sku="DEMO-DOCK",
                    name="USB-C Docking Station",
                    category_id=cat_hw.id,
                    list_price=Decimal("250.00"),
                    cost_price=Decimal("120.00"),
                    is_active=True,
                )
                session.add(p_dock)
                await session.flush()

            p_support = (await session.execute(select(Product).where(Product.sku == "DEMO-SUPPORT"))).scalar_one_or_none()
            if not p_support:
                p_support = Product(
                    sku="DEMO-SUPPORT",
                    name="24/7 Enterprise Support Plan",
                    category_id=cat_srv.id,
                    list_price=Decimal("500.00"),
                    cost_price=Decimal("100.00"),
                    is_active=True,
                )
                session.add(p_support)
                await session.flush()

            # 5. Warehouses & Inventory
            wh_main = (await session.execute(select(Warehouse).where(Warehouse.code == "WH-DEMO-MAIN"))).scalar_one_or_none()
            if not wh_main:
                wh_main = Warehouse(
                    code="WH-DEMO-MAIN",
                    name="Main Warehouse",
                    fulfillment_priority=1,
                    base_shipping_cost=Decimal("15.00"),
                    is_active=True,
                )
                session.add(wh_main)
                await session.flush()

            wh_east = (await session.execute(select(Warehouse).where(Warehouse.code == "WH-DEMO-EAST"))).scalar_one_or_none()
            if not wh_east:
                wh_east = Warehouse(
                    code="WH-DEMO-EAST",
                    name="East Depot",
                    fulfillment_priority=2,
                    base_shipping_cost=Decimal("25.00"),
                    is_active=True,
                )
                session.add(wh_east)
                await session.flush()

            inv_laptop_main = (await session.execute(select(Inventory).where(Inventory.warehouse_id == wh_main.id, Inventory.product_id == p_laptop.id))).scalar_one_or_none()
            if not inv_laptop_main:
                session.add(Inventory(warehouse_id=wh_main.id, product_id=p_laptop.id, on_hand_qty=Decimal("3.000"), reserved_qty=Decimal("0.000")))
            else:
                inv_laptop_main.on_hand_qty = Decimal("3.000")
                inv_laptop_main.reserved_qty = Decimal("0.000")

            inv_laptop_east = (await session.execute(select(Inventory).where(Inventory.warehouse_id == wh_east.id, Inventory.product_id == p_laptop.id))).scalar_one_or_none()
            if not inv_laptop_east:
                session.add(Inventory(warehouse_id=wh_east.id, product_id=p_laptop.id, on_hand_qty=Decimal("5.000"), reserved_qty=Decimal("0.000")))
            else:
                inv_laptop_east.on_hand_qty = Decimal("5.000")
                inv_laptop_east.reserved_qty = Decimal("0.000")

            inv_dock_main = (await session.execute(select(Inventory).where(Inventory.warehouse_id == wh_main.id, Inventory.product_id == p_dock.id))).scalar_one_or_none()
            if not inv_dock_main:
                session.add(Inventory(warehouse_id=wh_main.id, product_id=p_dock.id, on_hand_qty=Decimal("10.000"), reserved_qty=Decimal("0.000")))
            else:
                inv_dock_main.on_hand_qty = Decimal("10.000")
                inv_dock_main.reserved_qty = Decimal("0.000")

            # 6. Commercial Policies & Configs
            dp = (await session.execute(select(DiscountPolicy).where(DiscountPolicy.name == "DEMO-DISC-01"))).scalar_one_or_none()
            if not dp:
                session.add(DiscountPolicy(
                    name="DEMO-DISC-01",
                    standard_discount_pct=Decimal("5.00"),
                    max_discount_pct=Decimal("10.00"),
                    priority=100,
                    is_active=True,
                ))

            ap = (await session.execute(select(ApprovalPolicy).where(ApprovalPolicy.name == "DEMO-APP-01"))).scalar_one_or_none()
            if not ap:
                session.add(ApprovalPolicy(
                    name="DEMO-APP-01",
                    discount_above_pct=Decimal("10.00"),
                    approval_role="SALES_MANAGER",
                    priority=100,
                    is_active=True,
                ))

            bp_monthly = (await session.execute(select(BillingPlan).where(BillingPlan.code == "BP-DEMO-MONTHLY"))).scalar_one_or_none()
            if not bp_monthly:
                session.add(BillingPlan(
                    code="BP-DEMO-MONTHLY",
                    name="Demo Monthly Recurring Plan",
                    billing_type="RECURRING",
                    billing_interval_months=1,
                    proration_method="DAILY",
                    cancellation_method="END_OF_PERIOD",
                    is_active=True,
                ))

            bp_onetime = (await session.execute(select(BillingPlan).where(BillingPlan.code == "BP-DEMO-ONETIME"))).scalar_one_or_none()
            if not bp_onetime:
                session.add(BillingPlan(
                    code="BP-DEMO-ONETIME",
                    name="Demo One-Time Hardware Plan",
                    billing_type="ONE_TIME",
                    billing_interval_months=None,
                    proration_method="DAILY",
                    cancellation_method="END_OF_PERIOD",
                    is_active=True,
                ))

            dhc = (await session.execute(select(DealHealthConfig).where(DealHealthConfig.name == "DEMO-HEALTH-01"))).scalar_one_or_none()
            if not dhc:
                session.add(DealHealthConfig(
                    name="DEMO-HEALTH-01",
                    is_active=True,
                    healthy_min_score=Decimal("80.00"),
                    watch_min_score=Decimal("60.00"),
                    at_risk_min_score=Decimal("30.00"),
                    stalled_quote_days=5,
                    approval_delay_hours=24,
                    negotiation_stall_days=3,
                    discount_anomaly_threshold_pct=Decimal("10.00"),
                    delivery_slippage_days=2,
                    backorder_age_days=3,
                    invoice_overdue_days=1,
                ))

            # 7. Seed 3 Historical Quotes for Rep Baseline (5%, 7%, 8% discounts)
            for idx, disc in enumerate([Decimal("5.00"), Decimal("7.00"), Decimal("8.00")], start=1):
                h_num = f"QT-HIST-00{idx}"
                q_h = (await session.execute(select(Quotation).where(Quotation.quote_number == h_num))).scalar_one_or_none()
                if not q_h:
                    session.add(Quotation(
                        quote_number=h_num,
                        customer_id=customer.id,
                        sales_rep_id=u_rep.id,
                        status="CUSTOMER_CONFIRMED",
                        currency="USD",
                        net_total=Decimal("5000.00"),
                        order_discount_pct=disc,
                        weighted_effective_discount_pct=disc,
                        margin_pct=Decimal("35.00"),
                    ))

            await session.commit()

    print("=" * 60)
    print("DEALFLOW360 DEMO DATA BOOTSTRAP COMPLETE")
    print("=" * 60)
    print(f"Users created/ready: 5")
    print(f"  - Admin: admin.demo@example.com")
    print(f"  - Sales Manager: manager.demo@example.com")
    print(f"  - Finance Operations: finance.demo@example.com")
    print(f"  - Sales Rep: salesrep.demo@example.com")
    print(f"  - Customer Contact: customer.demo@example.com")
    print(f"Customer: Omega Corporation (DEMO-CUST-OMEGA)")
    print(f"Customer Portal Access: customer.demo@example.com -> DEMO-CUST-OMEGA")
    print(f"Products: Enterprise Laptop Pro, Docking Station, Support Plan")
    print(f"Warehouses: Main Warehouse (3 laptops), East Depot (5 laptops)")
    print(f"Historical Baseline: 3 confirmed quotes seeded (5%, 7%, 8% discounts)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(bootstrap_demo())
