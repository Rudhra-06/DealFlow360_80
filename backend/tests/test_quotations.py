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
from app.schemas.customer import CustomerCreate
from app.schemas.customer_tier import CustomerTierCreate
from app.schemas.discount_policy import DiscountPolicyCreate
from app.schemas.product import ProductCreate
from app.schemas.product_category import ProductCategoryCreate
from app.schemas.role import RoleCreateInternal
from app.services.customer import CustomerService
from app.services.customer_tier import CustomerTierService
from app.services.discount_policy import DiscountPolicyService
from app.services.product import ProductService
from app.services.product_category import ProductCategoryService
from app.services.user import UserService


@pytest.fixture
async def api_client(db_session: AsyncSession):
    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


async def get_user_token_and_id(db: AsyncSession, role_name: str):
    role_repo = RoleRepository()
    role = await role_repo.get_by_name(db, role_name)
    if not role:
        role = await role_repo.create_role(db, RoleCreateInternal(name=role_name))
        await db.commit()

    user_service = UserService(db)
    email = f"user-{uuid.uuid4().hex[:6]}@example.com"
    user = await user_service.create_user(
        email=email,
        full_name=f"Test User {role_name}",
        plain_password="TestUser123!",
        role_id=role.id,
    )
    token = create_access_token(subject=str(user.id))
    return token, user.id, user


@pytest.mark.anyio
async def test_quotation_end_to_end_acceptance_flow(db_session: AsyncSession, api_client: AsyncClient):
    token_admin, admin_id, _ = await get_user_token_and_id(db_session, RoleName.ADMIN)
    headers = {"Authorization": f"Bearer {token_admin}"}

    # 1. Setup Master Data
    tier_service = CustomerTierService(db_session)
    tier = await tier_service.create_tier(CustomerTierCreate(code=f"T-{uuid.uuid4().hex[:4]}", name="Gold Tier", is_active=True))

    cust_service = CustomerService(db_session)
    customer = await cust_service.create_customer(
        CustomerCreate(
            customer_code=f"C-{uuid.uuid4().hex[:4]}",
            name="Acme Corp",
            email=f"acme-{uuid.uuid4().hex[:4]}@example.com",
            currency="USD",
            tier_id=tier.id,
            is_active=True,
        )
    )

    cat_service = ProductCategoryService(db_session)
    category = await cat_service.create_category(ProductCategoryCreate(name=f"Cat-{uuid.uuid4().hex[:4]}", is_active=True))

    prod_service = ProductService(db_session)
    product_a = await prod_service.create_product(
        ProductCreate(
            sku=f"SKU-A-{uuid.uuid4().hex[:4]}",
            name="Product A",
            category_id=category.id,
            list_price=Decimal("100.00"),
            cost_price=Decimal("60.00"),
            currency="USD",
            is_active=True,
        )
    )
    product_b = await prod_service.create_product(
        ProductCreate(
            sku=f"SKU-B-{uuid.uuid4().hex[:4]}",
            name="Product B",
            category_id=category.id,
            list_price=Decimal("200.00"),
            cost_price=Decimal("120.00"),
            currency="USD",
            is_active=True,
        )
    )

    # Discount Policy: Product A standard 10%, max 20%
    policy_service = DiscountPolicyService(db_session)
    await policy_service.create_policy(
        DiscountPolicyCreate(
            name="Product A Policy",
            customer_tier_id=tier.id,
            product_id=product_a.id,
            standard_discount_pct=Decimal("10.00"),
            max_discount_pct=Decimal("20.00"),
            priority=10,
        )
    )

    # 2. Create Quotation
    resp = await api_client.post(
        "/api/v1/quotations",
        json={"customer_id": customer.id, "payment_terms_days": 30, "order_discount_pct": 0.00},
        headers=headers,
    )
    assert resp.status_code == 201
    quote_data = resp.json()
    quote_id = quote_data["id"]
    assert quote_data["status"] == "DRAFT"
    assert quote_data["currency"] == "USD"

    # 3. Add Product A (omitting line discount -> defaults to 10% from policy)
    resp = await api_client.post(
        f"/api/v1/quotations/{quote_id}/lines",
        json={"product_id": product_a.id, "quantity": 10.0},
        headers=headers,
    )
    assert resp.status_code == 201
    quote_data = resp.json()
    assert len(quote_data["lines"]) == 1
    line_a = quote_data["lines"][0]
    assert line_a["line_discount_pct"] == "10.00"
    assert line_a["unit_list_price"] == "100.00"
    assert line_a["unit_cost"] == "60.00"
    assert line_a["gross_line_total"] == "1000.00"
    assert line_a["net_line_total"] == "900.00"
    assert line_a["line_cost"] == "600.00"
    assert line_a["risk_level"] == "GREEN"

    # 4. Add Product B with explicit line discount = 25% (over max policy -> CORAL_RED)
    resp = await api_client.post(
        f"/api/v1/quotations/{quote_id}/lines",
        json={"product_id": product_b.id, "quantity": 5.0, "line_discount_pct": 25.00},
        headers=headers,
    )
    assert resp.status_code == 201
    quote_data = resp.json()
    assert len(quote_data["lines"]) == 2
    line_b = [l for l in quote_data["lines"] if l["product_id"] == product_b.id][0]
    assert line_b["line_discount_pct"] == "25.00"
    assert line_b["gross_line_total"] == "1000.00"
    assert line_b["net_line_total"] == "750.00"
    assert line_b["line_cost"] == "600.00"
    # No policy for Product B -> NO_APPLICABLE_DISCOUNT_POLICY (YELLOW)

    # 5. Update Order Discount to 5%
    resp = await api_client.patch(
        f"/api/v1/quotations/{quote_id}",
        json={"order_discount_pct": 5.00},
        headers=headers,
    )
    assert resp.status_code == 200
    quote_data = resp.json()
    assert quote_data["order_discount_pct"] == "5.00"

    # 6. Verify Pricing Snapshots remain intact after Product Master list price change
    product_a.list_price = Decimal("150.00")
    await db_session.commit()

    resp = await api_client.get(f"/api/v1/quotations/{quote_id}", headers=headers)
    assert resp.status_code == 200
    quote_data = resp.json()
    line_a_reloaded = [l for l in quote_data["lines"] if l["product_id"] == product_a.id][0]
    assert line_a_reloaded["unit_list_price"] == "100.00"  # Snapshot preserved!

    # 7. Check Audit Trail
    resp = await api_client.get(f"/api/v1/quotations/{quote_id}/audit", headers=headers)
    assert resp.status_code == 200
    audit_data = resp.json()
    event_types = [e["event_type"] for e in audit_data]
    assert "QUOTE_CREATED" in event_types
    assert "LINE_ADDED" in event_types
    assert "QUOTE_UPDATED" in event_types


@pytest.mark.anyio
async def test_quotation_rbac_and_ownership(db_session: AsyncSession, api_client: AsyncClient):
    token_rep1, rep1_id, _ = await get_user_token_and_id(db_session, RoleName.SALES_REP)
    token_rep2, rep2_id, _ = await get_user_token_and_id(db_session, RoleName.SALES_REP)
    headers_rep1 = {"Authorization": f"Bearer {token_rep1}"}
    headers_rep2 = {"Authorization": f"Bearer {token_rep2}"}

    tier_service = CustomerTierService(db_session)
    tier = await tier_service.create_tier(CustomerTierCreate(code=f"T-{uuid.uuid4().hex[:4]}", name="Tier RBAC"))
    cust_service = CustomerService(db_session)
    customer = await cust_service.create_customer(
        CustomerCreate(
            customer_code=f"C-{uuid.uuid4().hex[:4]}",
            name="RBAC Customer",
            email=f"rbac-{uuid.uuid4().hex[:4]}@example.com",
            tier_id=tier.id,
        )
    )

    # Rep 1 creates Quote
    resp = await api_client.post(
        "/api/v1/quotations",
        json={"customer_id": customer.id},
        headers=headers_rep1,
    )
    assert resp.status_code == 201
    quote_id = resp.json()["id"]

    # Rep 2 attempts to update Rep 1's quote -> 403 Forbidden
    resp = await api_client.patch(
        f"/api/v1/quotations/{quote_id}",
        json={"order_discount_pct": 2.00},
        headers=headers_rep2,
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_currency_mismatch_validation(db_session: AsyncSession, api_client: AsyncClient):
    token_admin, admin_id, _ = await get_user_token_and_id(db_session, RoleName.ADMIN)
    headers = {"Authorization": f"Bearer {token_admin}"}

    tier_service = CustomerTierService(db_session)
    tier = await tier_service.create_tier(CustomerTierCreate(code=f"T-{uuid.uuid4().hex[:4]}", name="Curr Tier"))
    cust_service = CustomerService(db_session)
    customer = await cust_service.create_customer(
        CustomerCreate(
            customer_code=f"C-{uuid.uuid4().hex[:4]}",
            name="USD Customer",
            email=f"usd-{uuid.uuid4().hex[:4]}@example.com",
            currency="USD",
            tier_id=tier.id,
        )
    )

    cat_service = ProductCategoryService(db_session)
    category = await cat_service.create_category(ProductCategoryCreate(name=f"Cat-{uuid.uuid4().hex[:4]}"))

    prod_service = ProductService(db_session)
    product_eur = await prod_service.create_product(
        ProductCreate(
            sku=f"SKU-EUR-{uuid.uuid4().hex[:4]}",
            name="EUR Product",
            category_id=category.id,
            list_price=Decimal("100.00"),
            cost_price=Decimal("60.00"),
            currency="EUR",
        )
    )

    resp = await api_client.post(
        "/api/v1/quotations",
        json={"customer_id": customer.id},
        headers=headers,
    )
    assert resp.status_code == 201
    quote_id = resp.json()["id"]

    # Add EUR product to USD quote -> 400 Bad Request
    resp = await api_client.post(
        f"/api/v1/quotations/{quote_id}/lines",
        json={"product_id": product_eur.id, "quantity": 1.0},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "does not match quotation currency" in resp.json()["detail"]
