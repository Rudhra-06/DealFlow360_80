import sys
import uuid
from decimal import Decimal
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.jwt import create_access_token
from app.core.roles import RoleName
from app.db.session import get_db
from app.main import app
from app.repositories.role import RoleRepository
from app.schemas.role import RoleCreateInternal
from app.services.user import UserService


async def get_or_create_role(db_session: AsyncSession, role_name: str):
    role_repo = RoleRepository()
    role = await role_repo.get_by_name(db_session, role_name)
    if not role:
        role = await role_repo.create_role(
            db_session, RoleCreateInternal(name=role_name)
        )
        await db_session.commit()
    return role


async def create_user_with_role(db_session: AsyncSession, role_name: str):
    role = await get_or_create_role(db_session, role_name)
    user_service = UserService(db_session)
    email = f"user-{role_name.lower()}-{uuid.uuid4().hex[:6]}@example.com"
    user = await user_service.create_user(
        email=email,
        full_name=f"{role_name} User",
        plain_password="SecurePassword123!",
        role_id=role.id,
    )
    token = create_access_token(subject=str(user.id))
    return user, token


@pytest.fixture
async def master_client(db_session: AsyncSession):
    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_full_master_data_acceptance_flow(
    db_session: AsyncSession, master_client: AsyncClient
):
    """Smoke test executing full master-data flow: Tier -> Customer -> Category -> Product -> Warehouse -> Inventory."""
    _, admin_token = await create_user_with_role(db_session, RoleName.ADMIN)
    _, sales_token = await create_user_with_role(db_session, RoleName.SALES_REP)
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    headers_sales = {"Authorization": f"Bearer {sales_token}"}

    uid = uuid.uuid4().hex[:6]

    # 1. Create Customer Tier (Admin)
    res_tier = await master_client.post(
        "/api/v1/customer-tiers",
        json={"name": f"GOLD_{uid}", "description": "Gold Tier Partner"},
        headers=headers_admin,
    )
    assert res_tier.status_code == 201
    tier_data = res_tier.json()
    tier_id = tier_data["id"]

    # 2. Create Customer (Admin)
    res_cust = await master_client.post(
        "/api/v1/customers",
        json={
            "customer_code": f"  cust-{uid}  ",
            "name": "Acme Global Enterprise",
            "email": f"acme-{uid}@example.com",
            "tier_id": tier_id,
            "credit_limit": "75000.00",
            "currency": "usd",
        },
        headers=headers_admin,
    )
    assert res_cust.status_code == 201
    cust_data = res_cust.json()
    assert cust_data["customer_code"] == f"CUST-{uid.upper()}"
    assert cust_data["tier"]["name"] == f"GOLD_{uid}"
    cust_id = cust_data["id"]

    # 3. Read Customer (Sales Rep)
    res_get_cust = await master_client.get(
        f"/api/v1/customers/{cust_id}", headers=headers_sales
    )
    assert res_get_cust.status_code == 200

    # 4. Create Product Category (Admin)
    res_cat = await master_client.post(
        "/api/v1/product-categories",
        json={"name": f"HARDWARE_{uid}", "description": "IT Hardware"},
        headers=headers_admin,
    )
    assert res_cat.status_code == 201
    cat_id = res_cat.json()["id"]

    # 5. Create Product (Admin)
    res_prod = await master_client.post(
        "/api/v1/products",
        json={
            "sku": f"  sku-prod-{uid}  ",
            "name": "Rack Server Unit",
            "category_id": cat_id,
            "list_price": "1500.00",
            "cost_price": "900.00",
        },
        headers=headers_admin,
    )
    assert res_prod.status_code == 201
    prod_data = res_prod.json()
    assert prod_data["sku"] == f"SKU-PROD-{uid.upper()}"
    prod_id = prod_data["id"]

    # 6. Create Warehouse (Admin)
    res_wh = await master_client.post(
        "/api/v1/warehouses",
        json={"code": f"  wh-main-{uid}  ", "name": "Chicago Central DC"},
        headers=headers_admin,
    )
    assert res_wh.status_code == 201
    wh_id = res_wh.json()["id"]

    # 7. Create Inventory (Admin)
    res_inv = await master_client.post(
        "/api/v1/inventory",
        json={
            "warehouse_id": wh_id,
            "product_id": prod_id,
            "on_hand_qty": "100.000",
            "reorder_level": "10.000",
        },
        headers=headers_admin,
    )
    assert res_inv.status_code == 201
    inv_data = res_inv.json()
    assert inv_data["on_hand_qty"] == "100.000"
    assert inv_data["reserved_qty"] == "0.000"
    assert inv_data["available_qty"] == "100.000"
    inv_id = inv_data["id"]

    # 8. Update Inventory on_hand_qty (Admin)
    res_patch_inv = await master_client.patch(
        f"/api/v1/inventory/{inv_id}",
        json={"on_hand_qty": "150.000"},
        headers=headers_admin,
    )
    assert res_patch_inv.status_code == 200
    assert res_patch_inv.json()["on_hand_qty"] == "150.000"
    assert res_patch_inv.json()["available_qty"] == "150.000"


@pytest.mark.anyio
async def test_customer_role_is_forbidden_on_master_data(
    db_session: AsyncSession, master_client: AsyncClient
):
    """Verify external CUSTOMER user receives HTTP 403 Forbidden on internal master-data endpoints."""
    _, customer_token = await create_user_with_role(db_session, RoleName.CUSTOMER)
    headers = {"Authorization": f"Bearer {customer_token}"}

    endpoints = [
        "/api/v1/customer-tiers",
        "/api/v1/customers",
        "/api/v1/product-categories",
        "/api/v1/products",
        "/api/v1/warehouses",
        "/api/v1/inventory",
    ]

    for ep in endpoints:
        res = await master_client.get(ep, headers=headers)
        assert res.status_code == 403
        assert res.json()["detail"] == "Insufficient permissions"


@pytest.mark.anyio
async def test_duplicate_code_returns_409_conflict(
    db_session: AsyncSession, master_client: AsyncClient
):
    """Verify duplicate customer code returns HTTP 409 Conflict."""
    _, admin_token = await create_user_with_role(db_session, RoleName.ADMIN)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create tier
    res_tier = await master_client.post(
        "/api/v1/customer-tiers",
        json={"name": f"TIER_DUP_{uuid.uuid4().hex[:6]}"},
        headers=headers,
    )
    tier_id = res_tier.json()["id"]

    code = f"CUST-DUP-{uuid.uuid4().hex[:6]}"

    # First customer create
    res1 = await master_client.post(
        "/api/v1/customers",
        json={"customer_code": code, "name": "First Customer", "tier_id": tier_id},
        headers=headers,
    )
    assert res1.status_code == 201

    # Second customer create with same code -> 409
    res2 = await master_client.post(
        "/api/v1/customers",
        json={"customer_code": code, "name": "Second Customer", "tier_id": tier_id},
        headers=headers,
    )
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]
