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
from app.core.security import get_password_hash
from app.models.role import Role, RoleName
from app.models.user import User
from app.models.customer_tier import CustomerTier
from app.models.customer import Customer
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
    stmt = select(Role).where(Role.name == name)
    res = await session.execute(stmt)
    role = res.scalar_one_or_none()
    if not role:
        role = Role(name=name, description=f"{name.value} role")
        session.add(role)
        await session.flush()
    return role


async def get_or_create_user(session: AsyncSession, email: str, full_name: str, role: Role) -> User:
    stmt = select(User).where(User.email == email)
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        pwd_hash = get_password_hash(DEMO_PASSWORD)
        user = User(email=email, password_hash=pwd_hash, full_name=full_name, is_active=True)
        user.roles.append(role)
        session.add(user)
        await session.flush()
    elif role not in user.roles:
        user.roles.append(role)
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
                tier = CustomerTier(name="Gold Enterprise", min_annual_spend=Decimal("100000.00"), discount_limit_pct=Decimal("15.00"))
                session.add(tier)
                await session.flush()

            c_stmt = select(Customer).where(Customer.customer_code == "DEMO-CUST-OMEGA")
            customer = (await session.execute(c_stmt)).scalar_one_or_none()
            if not customer:
                customer = Customer(
                    customer_code="DEMO-CUST-OMEGA",
                    company_name="Omega Corporation",
                    tier_id=tier.id,
                    assigned_sales_rep_id=u_rep.id,
                    is_active=True
                )
                session.add(customer)
                await session.flush()

            # 4. Categories & Products
            cat_hw = (await session.execute(select(ProductCategory).where(ProductCategory.name == "Hardware"))).scalar_one_or_none()
            if not cat_hw:
                cat_hw = ProductCategory(name="Hardware", description="Enterprise Hardware")
                session.add(cat_hw)
                await session.flush()

            cat_srv = (await session.execute(select(ProductCategory).where(ProductCategory.name == "Services"))).scalar_one_or_none()
            if not cat_srv:
                cat_srv = ProductCategory(name="Services", description="Professional Services & Support")
                session.add(cat_srv)
                await session.flush()

            p_laptop = (await session.execute(select(Product).where(Product.sku == "DEMO-LAPTOP"))).scalar_one_or_none()
            if not p_laptop:
                p_laptop = Product(sku="DEMO-LAPTOP", name="Enterprise Laptop Pro", category_id=cat_hw.id, list_price=Decimal("1500.00"), cost_price=Decimal("900.00"), is_active=True)
                session.add(p_laptop)
                await session.flush()

            p_dock = (await session.execute(select(Product).where(Product.sku == "DEMO-DOCK"))).scalar_one_or_none()
            if not p_dock:
                p_dock = Product(sku="DEMO-DOCK", name="USB-C Docking Station", category_id=cat_hw.id, list_price=Decimal("250.00"), cost_price=Decimal("120.00"), is_active=True)
                session.add(p_dock)
                await session.flush()

            p_support = (await session.execute(select(Product).where(Product.sku == "DEMO-SUPPORT"))).scalar_one_or_none()
            if not p_support:
                p_support = Product(sku="DEMO-SUPPORT", name="24/7 Enterprise Support Plan", category_id=cat_srv.id, list_price=Decimal("500.00"), cost_price=Decimal("100.00"), is_active=True)
                session.add(p_support)
                await session.flush()

            # 5. Warehouses & Inventory
            wh_main = (await session.execute(select(Warehouse).where(Warehouse.code == "WH-DEMO-MAIN"))).scalar_one_or_none()
            if not wh_main:
                wh_main = Warehouse(code="WH-DEMO-MAIN", name="Main Warehouse", priority=1, base_shipping_cost=Decimal("15.00"), is_active=True)
                session.add(wh_main)
                await session.flush()

            wh_east = (await session.execute(select(Warehouse).where(Warehouse.code == "WH-DEMO-EAST"))).scalar_one_or_none()
            if not wh_east:
                wh_east = Warehouse(code="WH-DEMO-EAST", name="East Depot", priority=2, base_shipping_cost=Decimal("25.00"), is_active=True)
                session.add(wh_east)
                await session.flush()

            inv_laptop_main = (await session.execute(select(Inventory).where(Inventory.warehouse_id == wh_main.id, Inventory.product_id == p_laptop.id))).scalar_one_or_none()
            if not inv_laptop_main:
                session.add(Inventory(warehouse_id=wh_main.id, product_id=p_laptop.id, quantity_on_hand=3, quantity_reserved=0))

            inv_laptop_east = (await session.execute(select(Inventory).where(Inventory.warehouse_id == wh_east.id, Inventory.product_id == p_laptop.id))).scalar_one_or_none()
            if not inv_laptop_east:
                session.add(Inventory(warehouse_id=wh_east.id, product_id=p_laptop.id, quantity_on_hand=5, quantity_reserved=0))

            inv_dock_main = (await session.execute(select(Inventory).where(Inventory.warehouse_id == wh_main.id, Inventory.product_id == p_dock.id))).scalar_one_or_none()
            if not inv_dock_main:
                session.add(Inventory(warehouse_id=wh_main.id, product_id=p_dock.id, quantity_on_hand=10, quantity_reserved=0))

            # 6. Commercial Policies & Configs
            dp = (await session.execute(select(DiscountPolicy).where(DiscountPolicy.name == "DEMO-DISC-01"))).scalar_one_or_none()
            if not dp:
                session.add(DiscountPolicy(name="DEMO-DISC-01", max_discount_pct=Decimal("10.00"), is_active=True))

            ap = (await session.execute(select(ApprovalPolicy).where(ApprovalPolicy.name == "DEMO-APP-01"))).scalar_one_or_none()
            if not ap:
                session.add(ApprovalPolicy(name="DEMO-APP-01", min_discount_pct=Decimal("10.01"), required_role="SALES_MANAGER", is_active=True))

            bp = (await session.execute(select(BillingPlan).where(BillingPlan.name == "DEMO-BILL-01"))).scalar_one_or_none()
            if not bp:
                session.add(BillingPlan(name="DEMO-BILL-01", billing_frequency="MONTHLY", advance_notice_days=5, is_active=True))

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
                q_h = (await session.execute(select(Quotation).where(Quotation.quotation_number == h_num))).scalar_one_or_none()
                if not q_h:
                    session.add(Quotation(
                        quotation_number=h_num,
                        customer_id=customer.id,
                        sales_rep_id=u_rep.id,
                        status="CUSTOMER_CONFIRMED",
                        currency="USD",
                        net_total=Decimal("5000.00"),
                        effective_discount_pct=disc,
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
    print(f"Products: Enterprise Laptop Pro, Docking Station, Support Plan")
    print(f"Warehouses: Main Warehouse (3 laptops), East Depot (5 laptops)")
    print(f"Historical Baseline: 3 confirmed quotes seeded (5%, 7%, 8% discounts)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(bootstrap_demo())
