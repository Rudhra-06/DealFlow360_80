import sys
import uuid
from decimal import Decimal
from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app.core.jwt import create_access_token
from app.core.roles import RoleName
from app.db.session import get_db
from app.repositories.role import RoleRepository
from app.schemas.role import RoleCreateInternal
from app.services.user import UserService


@pytest.fixture
async def api_client(db_session: AsyncSession):
    """Provides AsyncClient bound to app with DB session override."""
    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


async def get_user_token(db: AsyncSession, role_name: str) -> str:
    role_repo = RoleRepository()
    role = await role_repo.get_by_name(db, role_name)
    if not role:
        role = await role_repo.create_role(db, RoleCreateInternal(name=role_name))
        await db.commit()

    user_service = UserService(db)
    user = await user_service.create_user(
        email=f"user-{role_name.lower()}-{uuid.uuid4().hex[:6]}@example.com",
        full_name=f"User {role_name}",
        plain_password="Password123!",
        role_id=role.id,
    )
    return create_access_token(subject=str(user.id))


@pytest.mark.anyio
async def test_discount_policy_crud_and_rbac(db_session: AsyncSession, api_client: AsyncClient):
    """Verify DiscountPolicy REST API endpoints and RBAC write restrictions."""
    admin_token = await get_user_token(db_session, RoleName.ADMIN)
    rep_token = await get_user_token(db_session, RoleName.SALES_REP)
    customer_token = await get_user_token(db_session, RoleName.CUSTOMER)

    # 1. Admin creates discount policy -> HTTP 201
    p_name = f"API Discount {uuid.uuid4().hex[:6]}"
    res_create = await api_client.post(
        "/api/v1/discount-policies",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": p_name,
            "standard_discount_pct": 5.0,
            "max_discount_pct": 15.0,
            "priority": 50,
        },
    )
    assert res_create.status_code == 201
    policy_id = res_create.json()["id"]

    # 2. Sales Rep reads discount policy -> HTTP 200
    res_get = await api_client.get(
        f"/api/v1/discount-policies/{policy_id}",
        headers={"Authorization": f"Bearer {rep_token}"},
    )
    assert res_get.status_code == 200
    assert res_get.json()["name"] == p_name

    # 3. Sales Rep attempts write -> HTTP 403 Forbidden
    res_rep_write = await api_client.post(
        "/api/v1/discount-policies",
        headers={"Authorization": f"Bearer {rep_token}"},
        json={
            "name": "Unauthorized Rep Policy",
            "standard_discount_pct": 2.0,
            "max_discount_pct": 5.0,
        },
    )
    assert res_rep_write.status_code == 403

    # 4. Customer attempts read -> HTTP 403 Forbidden
    res_cust_read = await api_client.get(
        f"/api/v1/discount-policies/{policy_id}",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert res_cust_read.status_code == 403


@pytest.mark.anyio
async def test_approval_policy_crud_and_rbac(db_session: AsyncSession, api_client: AsyncClient):
    """Verify ApprovalPolicy REST API endpoints and RBAC write restrictions."""
    mgr_token = await get_user_token(db_session, RoleName.SALES_MANAGER)
    rep_token = await get_user_token(db_session, RoleName.SALES_REP)

    # 1. Manager creates approval policy -> HTTP 201
    res_create = await api_client.post(
        "/api/v1/approval-policies",
        headers={"Authorization": f"Bearer {mgr_token}"},
        json={
            "name": "Manager Approval > 15%",
            "discount_above_pct": 15.0,
            "approval_role": RoleName.SALES_MANAGER,
        },
    )
    assert res_create.status_code == 201
    policy_id = res_create.json()["id"]

    # 2. Sales Rep attempts approval policy write -> HTTP 403 Forbidden
    res_rep_write = await api_client.post(
        "/api/v1/approval-policies",
        headers={"Authorization": f"Bearer {rep_token}"},
        json={
            "name": "Rep Unauthorized Approval",
            "discount_above_pct": 5.0,
            "approval_role": RoleName.SALES_MANAGER,
        },
    )
    assert res_rep_write.status_code == 403


@pytest.mark.anyio
async def test_billing_plan_crud_and_rbac(db_session: AsyncSession, api_client: AsyncClient):
    """Verify BillingPlan REST API endpoints and RBAC write restrictions."""
    fin_token = await get_user_token(db_session, RoleName.FINANCE_OPERATIONS)
    mgr_token = await get_user_token(db_session, RoleName.SALES_MANAGER)

    code = f"QUARTERLY_{uuid.uuid4().hex[:6]}"

    # 1. Finance creates recurring billing plan -> HTTP 201
    res_create = await api_client.post(
        "/api/v1/billing-plans",
        headers={"Authorization": f"Bearer {fin_token}"},
        json={
            "code": code,
            "name": "Quarterly Billing Plan",
            "billing_type": "RECURRING",
            "billing_interval_months": 3,
            "payment_due_days": 30,
        },
    )
    assert res_create.status_code == 201
    assert res_create.json()["code"] == code.upper()

    # 2. Manager attempts billing plan write -> HTTP 403 Forbidden (Finance / Admin only)
    res_mgr_write = await api_client.post(
        "/api/v1/billing-plans",
        headers={"Authorization": f"Bearer {mgr_token}"},
        json={
            "code": f"MGR_PLAN_{uuid.uuid4().hex[:6]}",
            "name": "Manager Plan",
            "billing_type": "ONE_TIME",
        },
    )
    assert res_mgr_write.status_code == 403
