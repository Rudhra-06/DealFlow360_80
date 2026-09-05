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
from app.schemas.approval_policy import ApprovalPolicyCreate
from app.schemas.customer import CustomerCreate
from app.schemas.customer_tier import CustomerTierCreate
from app.schemas.discount_policy import DiscountPolicyCreate
from app.schemas.product import ProductCreate
from app.schemas.product_category import ProductCategoryCreate
from app.schemas.product_recommendation_rule import RecommendationRuleCreate
from app.schemas.role import RoleCreateInternal
from app.services.approval_policy import ApprovalPolicyService
from app.services.customer import CustomerService
from app.services.customer_tier import CustomerTierService
from app.services.discount_policy import DiscountPolicyService
from app.services.product import ProductService
from app.services.product_category import ProductCategoryService
from app.services.product_recommendation_rule import ProductRecommendationRuleService
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


async def create_user_with_role(db: AsyncSession, role_name: str):
    role_repo = RoleRepository()
    role = await role_repo.get_by_name(db, role_name)
    if not role:
        role = await role_repo.create_role(db, RoleCreateInternal(name=role_name))
        await db.commit()

    user_service = UserService(db)
    email = f"{role_name.lower()}-{uuid.uuid4().hex[:6]}@example.com"
    user = await user_service.create_user(
        email=email,
        full_name=f"User {role_name}",
        plain_password="TestUser123!",
        role_id=role.id,
    )
    token = create_access_token(subject=str(user.id))
    return token, user


@pytest.mark.anyio
async def test_phase3_complete_end_to_end_acceptance_flow(db_session: AsyncSession, api_client: AsyncClient):
    token_rep, user_rep = await create_user_with_role(db_session, RoleName.SALES_REP)
    token_mgr, user_mgr = await create_user_with_role(db_session, RoleName.SALES_MANAGER)
    token_fin, user_fin = await create_user_with_role(db_session, RoleName.FINANCE_OPERATIONS)
    token_admin, user_admin = await create_user_with_role(db_session, RoleName.ADMIN)

    headers_rep = {"Authorization": f"Bearer {token_rep}"}
    headers_mgr = {"Authorization": f"Bearer {token_mgr}"}
    headers_fin = {"Authorization": f"Bearer {token_fin}"}

    # 1. Setup Master Data & Policies
    tier_service = CustomerTierService(db_session)
    tier = await tier_service.create_tier(CustomerTierCreate(code=f"T-{uuid.uuid4().hex[:4]}", name="Platinum Tier"))

    cust_service = CustomerService(db_session)
    customer = await cust_service.create_customer(
        CustomerCreate(
            customer_code=f"C-{uuid.uuid4().hex[:4]}",
            name="OmniCorp",
            email=f"omni-{uuid.uuid4().hex[:4]}@example.com",
            currency="USD",
            tier_id=tier.id,
        )
    )

    cat_service = ProductCategoryService(db_session)
    cat_hw = await cat_service.create_category(ProductCategoryCreate(name=f"Hardware-{uuid.uuid4().hex[:4]}"))
    cat_srv = await cat_service.create_category(ProductCategoryCreate(name=f"Services-{uuid.uuid4().hex[:4]}"))

    prod_service = ProductService(db_session)
    prod_hw = await prod_service.create_product(
        ProductCreate(
            sku=f"HW-{uuid.uuid4().hex[:4]}",
            name="Server Hardware",
            category_id=cat_hw.id,
            list_price=Decimal("1000.00"),
            cost_price=Decimal("600.00"),
            currency="USD",
        )
    )
    prod_srv = await prod_service.create_product(
        ProductCreate(
            sku=f"SRV-{uuid.uuid4().hex[:4]}",
            name="Maintenance Service",
            category_id=cat_srv.id,
            list_price=Decimal("500.00"),
            cost_price=Decimal("200.00"),
            currency="USD",
        )
    )
    prod_acc = await prod_service.create_product(
        ProductCreate(
            sku=f"ACC-{uuid.uuid4().hex[:4]}",
            name="Rack Mount Kit",
            category_id=cat_hw.id,
            list_price=Decimal("100.00"),
            cost_price=Decimal("40.00"),
            currency="USD",
        )
    )

    # Discount Policies
    disc_service = DiscountPolicyService(db_session)
    await disc_service.create_policy(
        DiscountPolicyCreate(
            name="Hardware Discount Policy",
            product_id=prod_hw.id,
            standard_discount_pct=Decimal("10.00"),
            max_discount_pct=Decimal("15.00"),
        )
    )
    await disc_service.create_policy(
        DiscountPolicyCreate(
            name="Services Discount Policy",
            product_id=prod_srv.id,
            standard_discount_pct=Decimal("5.00"),
            max_discount_pct=Decimal("10.00"),
        )
    )

    # Approval Policies
    app_service = ApprovalPolicyService(db_session)
    await app_service.create_policy(
        ApprovalPolicyCreate(
            name="Manager Discount Policy",
            discount_above_pct=Decimal("12.00"),
            approval_role=RoleName.SALES_MANAGER.value,
            priority=100,
        )
    )
    await app_service.create_policy(
        ApprovalPolicyCreate(
            name="Finance Blended Risk Policy",
            blended_risk_above=Decimal("2.00"),
            approval_role=RoleName.FINANCE_OPERATIONS.value,
            priority=50,
        )
    )

    # Recommendation Rule: Hardware -> Rack Mount Kit
    rec_rule_service = ProductRecommendationRuleService(db_session)
    rec_rule = await rec_rule_service.create_rule(
        RecommendationRuleCreate(
            source_product_id=prod_hw.id,
            suggested_product_id=prod_acc.id,
            affinity_score=Decimal("3.00"),
            recommended_qty=Decimal("2.000"),
            is_promoted=True,
            promotion_label="Recommended Accessory",
            min_margin_pct=Decimal("20.00"),
        )
    )

    # 2. Create Draft Quotation
    resp = await api_client.post("/api/v1/quotations", json={"customer_id": customer.id}, headers=headers_rep)
    assert resp.status_code == 201
    quote_id = resp.json()["id"]

    # 3. Add Hardware Line (10% discount)
    resp = await api_client.post(f"/api/v1/quotations/{quote_id}/lines", json={"product_id": prod_hw.id, "quantity": 2.0}, headers=headers_rep)
    assert resp.status_code == 201

    # 4. Add Service Line (18% discount -> exceeds max 10%!)
    resp = await api_client.post(f"/api/v1/quotations/{quote_id}/lines", json={"product_id": prod_srv.id, "quantity": 1.0, "line_discount_pct": 18.00}, headers=headers_rep)
    assert resp.status_code == 201

    # 5. Fetch Upsell Recommendation
    resp = await api_client.get(f"/api/v1/quotations/{quote_id}/recommendations", headers=headers_rep)
    assert resp.status_code == 200
    recs = resp.json()
    assert len(recs) >= 1
    assert recs[0]["suggested_product_id"] == prod_acc.id

    # 6. Add Recommended Product to Quote
    resp = await api_client.post(f"/api/v1/quotations/{quote_id}/recommendations/{rec_rule.id}/add", headers=headers_rep)
    assert resp.status_code == 200
    quote_data = resp.json()
    assert len(quote_data["lines"]) == 3

    # 7. What-If Simulator (Non-Persistent test)
    resp = await api_client.post(
        f"/api/v1/quotations/{quote_id}/what-if",
        json={"order_discount_pct": 5.00},
        headers=headers_rep,
    )
    assert resp.status_code == 200
    what_if_res = resp.json()
    assert what_if_res["persisted"] is False
    assert "PENDING_MANAGER_APPROVAL" in what_if_res["after"]["projected_status"]

    # Verify DB quote remains untouched after What-If
    resp = await api_client.get(f"/api/v1/quotations/{quote_id}", headers=headers_rep)
    assert resp.json()["order_discount_pct"] == "0.00"

    # 8. Submit Quotation -> Triggers 2-level Approval Routing (Manager -> Finance)
    resp = await api_client.post(f"/api/v1/quotations/{quote_id}/submit", headers=headers_rep)
    assert resp.status_code == 200
    sub_res = resp.json()
    assert sub_res["status"] == "PENDING_MANAGER_APPROVAL"
    assert sub_res["required_roles"] == [RoleName.SALES_MANAGER.value, RoleName.FINANCE_OPERATIONS.value]

    # Fetch approval steps
    resp = await api_client.get(f"/api/v1/quotations/{quote_id}/approvals", headers=headers_rep)
    assert resp.status_code == 200
    steps = resp.json()
    assert len(steps) == 2
    mgr_step = [s for s in steps if s["approval_role"] == RoleName.SALES_MANAGER.value][0]
    fin_step = [s for s in steps if s["approval_role"] == RoleName.FINANCE_OPERATIONS.value][0]
    assert mgr_step["status"] == "PENDING"
    assert fin_step["status"] == "PENDING"

    # 9. Manager Approves Step 1
    resp = await api_client.post(
        f"/api/v1/quotations/{quote_id}/approvals/{mgr_step['id']}/approve",
        json={"reason": "Approved hardware discount by Sales Manager"},
        headers=headers_mgr,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "PENDING_FINANCE_APPROVAL"

    # 10. Finance Approves Step 2
    resp = await api_client.post(
        f"/api/v1/quotations/{quote_id}/approvals/{fin_step['id']}/approve",
        json={"reason": "Approved risk overage by Finance Operations"},
        headers=headers_fin,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "APPROVED"

    # 11. Audit History Complete Verification
    resp = await api_client.get(f"/api/v1/quotations/{quote_id}/audit", headers=headers_rep)
    assert resp.status_code == 200
    audit_events = resp.json()
    event_types = [e["event_type"] for e in audit_events]
    assert "QUOTE_CREATED" in event_types
    assert "LINE_ADDED" in event_types
    assert "UPSELL_ADDED" in event_types
    assert "QUOTE_SUBMITTED" in event_types
    assert "APPROVAL_APPROVED" in event_types
