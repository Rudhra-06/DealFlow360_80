import asyncio
import sys
from pathlib import Path

# Ensure backend root directory is in sys.path when running script directly
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.role import Role

DEFAULT_ROLES = [
    {"name": "ADMIN", "description": "System Administrator with full management access."},
    {"name": "SALES_REP", "description": "Sales Representative creating quotes and interacting with clients."},
    {"name": "SALES_MANAGER", "description": "Sales Manager reviewing and approving commercial deals."},
    {"name": "FINANCE_OPERATIONS", "description": "Finance and Operations member managing discount exceptions, fulfillment, and billing."},
    {"name": "CUSTOMER", "description": "External Customer portal access for quote negotiations."},
]


async def seed_roles() -> None:
    """Idempotently seed default DealFlow360 roles into PostgreSQL database."""
    async with AsyncSessionLocal() as session:
        async with session.begin():
            for role_data in DEFAULT_ROLES:
                stmt = select(Role).where(Role.name == role_data["name"])
                existing_role = (await session.execute(stmt)).scalar_one_or_none()
                if not existing_role:
                    new_role = Role(
                        name=role_data["name"],
                        description=role_data["description"],
                    )
                    session.add(new_role)
                    print(f"[SEED] Added role: {role_data['name']}")
                else:
                    print(f"[SEED] Role already exists: {role_data['name']}")
        await session.commit()
    print("[SEED] Role seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed_roles())
