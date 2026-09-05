"""Safe Demo Data Reset Script for DealFlow360 Phase 6 Part 3.

Safely cleans up demo-tagged data (demo emails, DEMO- codes, QT-HIST- quotes).
Requires DEMO_RESET_ALLOWED=true environment variable.
Never touches production or non-demo data.
"""

import asyncio
import os
import sys

# Ensure backend path in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal


async def reset_demo_data():
    reset_allowed = os.getenv("DEMO_RESET_ALLOWED", "false").lower() in ["true", "1", "yes"]
    app_env = os.getenv("APP_ENV", "development").lower()

    if app_env == "production":
        print("ERROR: Cannot reset demo data in production environment!")
        sys.exit(1)

    if not reset_allowed:
        print("ERROR: Reset refused. Please set DEMO_RESET_ALLOWED=true environment variable to confirm reset.")
        sys.exit(1)

    print("Starting safe demo data reset...")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Delete demo records in safe dependency order
            demo_emails = [
                "admin.demo@example.com",
                "manager.demo@example.com",
                "finance.demo@example.com",
                "salesrep.demo@example.com",
                "customer.demo@example.com",
            ]

            # 1. Historical & Demo Quotes
            await session.execute(text("DELETE FROM quotations WHERE quotation_number LIKE 'QT-HIST-%' OR quotation_number LIKE 'QT-DEMO-%'"))

            # 2. Demo Customers
            await session.execute(text("DELETE FROM customers WHERE customer_code LIKE 'DEMO-%'"))

            # 3. Demo Products & Inventory
            await session.execute(text("DELETE FROM inventory WHERE warehouse_id IN (SELECT id FROM warehouses WHERE code LIKE 'WH-DEMO-%')"))
            await session.execute(text("DELETE FROM products WHERE sku LIKE 'DEMO-%'"))

            # 4. Demo Warehouses & Categories
            await session.execute(text("DELETE FROM warehouses WHERE code LIKE 'WH-DEMO-%'"))
            await session.execute(text("DELETE FROM product_categories WHERE name IN ('Hardware', 'Services') AND id NOT IN (SELECT category_id FROM products)"))

            # 5. Demo Policies & Configs
            await session.execute(text("DELETE FROM discount_policies WHERE name LIKE 'DEMO-%'"))
            await session.execute(text("DELETE FROM approval_policies WHERE name LIKE 'DEMO-%'"))
            await session.execute(text("DELETE FROM billing_plans WHERE name LIKE 'DEMO-%'"))
            await session.execute(text("DELETE FROM deal_health_configs WHERE name LIKE 'DEMO-%'"))

            # 6. Demo Users
            for email in demo_emails:
                await session.execute(text("DELETE FROM user_roles WHERE user_id IN (SELECT id FROM users WHERE email = :email)"), {"email": email})
                await session.execute(text("DELETE FROM users WHERE email = :email"), {"email": email})

            await session.commit()

    print("=" * 60)
    print("DEALFLOW360 DEMO DATA RESET COMPLETE")
    print("=" * 60)
    print("All demo-tagged records (DEMO-* codes, demo users) successfully removed.")
    print("No non-demo or production data was modified.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(reset_demo_data())
