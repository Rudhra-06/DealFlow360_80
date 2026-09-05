import asyncio
import sys
from pathlib import Path

# Ensure backend root directory is in sys.path when running script directly
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.roles import RoleName
from app.db.session import AsyncSessionLocal
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.schemas.role import RoleCreateInternal
from app.services.exceptions import UserAlreadyExistsError
from app.services.role import RoleService
from app.services.user import UserService

# Define 5 canonical roles and matching demo identities
DEMO_IDENTITIES = [
    {
        "role_name": RoleName.ADMIN,
        "role_description": "System Administrator with full management access.",
        "email": "admin.demo@example.com",
        "full_name": "Demo Admin User",
    },
    {
        "role_name": RoleName.SALES_REP,
        "role_description": "Sales Representative creating quotes and interacting with clients.",
        "email": "salesrep.demo@example.com",
        "full_name": "Demo Sales Representative",
    },
    {
        "role_name": RoleName.SALES_MANAGER,
        "role_description": "Sales Manager reviewing and approving commercial deals.",
        "email": "manager.demo@example.com",
        "full_name": "Demo Sales Manager",
    },
    {
        "role_name": RoleName.FINANCE_OPERATIONS,
        "role_description": "Finance and Operations member managing discount exceptions, fulfillment, and billing.",
        "email": "finance.demo@example.com",
        "full_name": "Demo Finance Operations",
    },
    {
        "role_name": RoleName.CUSTOMER,
        "role_description": "External Customer portal access for quote negotiations.",
        "email": "customer.demo@example.com",
        "full_name": "Demo Customer User",
    },
]

INVALID_PASSWORDS = {
    "",
    "replace-with-local-demo-password",
    "admin123",
    "password",
    "123456",
}


async def bootstrap_demo_users() -> None:
    """Idempotently bootstrap standard roles and login-ready demo users into PostgreSQL."""
    demo_password = settings.DEMO_USER_PASSWORD.strip() if settings.DEMO_USER_PASSWORD else ""

    if not demo_password or demo_password in INVALID_PASSWORDS:
        print("[BOOTSTRAP ERROR] DEMO_USER_PASSWORD is missing or set to an insecure default placeholder.")
        print("[BOOTSTRAP ERROR] Please set DEMO_USER_PASSWORD in backend/.env to a secure value before running bootstrap.")
        sys.exit(1)

    print("[BOOTSTRAP] Starting DealFlow360 Phase 1 Demo Identity Seeding...")

    async with AsyncSessionLocal() as session:
        role_service = RoleService(session)
        user_repo = UserRepository()
        user_service = UserService(session)

        for identity in DEMO_IDENTITIES:
            r_name = identity["role_name"]
            r_desc = identity["role_description"]
            email = identity["email"]
            full_name = identity["full_name"]

            # 1. Ensure Role exists
            role = await role_service.get_role_by_name(r_name)
            if not role:
                role_repo = RoleRepository()
                role = await role_repo.create_role(
                    session,
                    RoleCreateInternal(name=r_name, description=r_desc)
                )
                await session.commit()
                print(f"[BOOTSTRAP] Role created: {r_name}")
            else:
                print(f"[BOOTSTRAP] Role exists: {r_name}")

            # 2. Check if Demo User exists
            existing_user = await user_repo.get_by_email(session, email.strip().lower())
            if existing_user:
                print(f"[BOOTSTRAP] Demo user already exists: {email}")
                if existing_user.role_id != role.id:
                    print(
                        f"[BOOTSTRAP WARNING] User {email} has role_id={existing_user.role_id}, "
                        f"which differs from expected role {r_name} (id={role.id}). Account role left unchanged."
                    )
                continue

            # 3. Create missing Demo User using UserService
            try:
                created_user = await user_service.create_user(
                    email=email,
                    full_name=full_name,
                    plain_password=demo_password,
                    role_id=role.id,
                )
                print(f"[BOOTSTRAP] Demo user created successfully: {created_user.email} (Role: {r_name})")
            except UserAlreadyExistsError:
                print(f"[BOOTSTRAP] Demo user already exists: {email}")
            except Exception as e:
                print(f"[BOOTSTRAP ERROR] Failed to create user {email}: {e}")

    print("[BOOTSTRAP] Phase 1 Demo Identity Seeding Complete.")


if __name__ == "__main__":
    asyncio.run(bootstrap_demo_users())
