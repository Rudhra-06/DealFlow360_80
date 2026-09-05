import pytest
from decimal import Decimal
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.enums import QuotationStatus
from app.core.roles import RoleName
from app.core.security import hash_password
from app.main import app
from app.db.session import get_db
from app.models.customer import Customer
from app.models.customer_portal_access import CustomerPortalAccess
from app.models.customer_tier import CustomerTier
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.role import Role
from app.models.user import User


async def get_or_create_role(db_session, role_name: str):
    res = await db_session.execute(select(Role).where(Role.name == role_name))
    role = res.scalar_one_or_none()
    if not role:
        role = Role(name=role_name, description=role_name)
        db_session.add(role)
        await db_session.flush()
    return role


async def get_or_create_tier(db_session):
    res = await db_session.execute(select(CustomerTier))
    tier = res.scalars().first()
    if not tier:
        tier = CustomerTier(name="Standard Tier", description="Standard Tier")
        db_session.add(tier)
        await db_session.flush()
    return tier


async def get_or_create_category(db_session):
    res = await db_session.execute(select(ProductCategory))
    cat = res.scalars().first()
    if not cat:
        cat = ProductCategory(name="General Category")
        db_session.add(cat)
        await db_session.flush()
    return cat


@pytest.mark.asyncio
async def test_phase4_full_integration_negotiation_to_confirmation(db_session):
    # Fetch pre-seeded / setup roles
    role_admin = await get_or_create_role(db_session, RoleName.ADMIN)
    role_rep = await get_or_create_role(db_session, RoleName.SALES_REP)
    role_mgr = await get_or_create_role(db_session, RoleName.SALES_MANAGER)
    role_cust = await get_or_create_role(db_session, RoleName.CUSTOMER)
    tier = await get_or_create_tier(db_session)
    cat = await get_or_create_category(db_session)

    # Setup users
    pass_hash = hash_password("password123")
    user_rep = User(email="rep_p4@example.com", hashed_password=pass_hash, full_name="Rep P4", role_id=role_rep.id)
    user_mgr = User(email="mgr_p4@example.com", hashed_password=pass_hash, full_name="Mgr P4", role_id=role_mgr.id)
    user_cust = User(email="cust_p4@example.com", hashed_password=pass_hash, full_name="Cust P4", role_id=role_cust.id)
    db_session.add_all([user_rep, user_mgr, user_cust])
    await db_session.flush()

    # Customer & Portal Access Mapping
    customer = Customer(customer_code="CUST-P4-FULL", name="Omega Corp", email="o@corp.com", tier_id=tier.id)
    db_session.add(customer)
    await db_session.flush()

    access = CustomerPortalAccess(user_id=user_cust.id, customer_id=customer.id, is_active=True)
    db_session.add(access)

    # Product
    prod = Product(sku="P4-SERVER", name="Enterprise Server", category_id=cat.id, list_price=Decimal("2000.00"), cost_price=Decimal("800.00"))
    db_session.add(prod)
    await db_session.commit()

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override

    try:
        # HTTP Async Client setup
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Login Rep
            res_rep_login = await client.post("/api/v1/auth/login", json={"email": "rep_p4@example.com", "password": "password123"})
            token_rep = res_rep_login.json()["access_token"]
            headers_rep = {"Authorization": f"Bearer {token_rep}"}

            # Login Customer
            res_cust_login = await client.post("/api/v1/auth/login", json={"email": "cust_p4@example.com", "password": "password123"})
            token_cust = res_cust_login.json()["access_token"]
            headers_cust = {"Authorization": f"Bearer {token_cust}"}

            # 1. Sales Rep creates draft quote & line
            r_create = await client.post("/api/v1/quotations", json={"customer_id": customer.id}, headers=headers_rep)
            assert r_create.status_code == 201
            quote_id = r_create.json()["id"]

            r_line = await client.post(
                f"/api/v1/quotations/{quote_id}/lines",
                json={"product_id": prod.id, "quantity": 1.0},
                headers=headers_rep,
            )
            assert r_line.status_code == 201

            # 2. Sales Rep submits quotation (auto-approved, no triggers)
            r_sub = await client.post(f"/api/v1/quotations/{quote_id}/submit", headers=headers_rep)
            assert r_sub.status_code == 200
            assert r_sub.json()["status"] == QuotationStatus.APPROVED.value

            # 3. Sales Rep sends approved quote to customer
            r_send = await client.post(f"/api/v1/quotations/{quote_id}/send-to-customer", headers=headers_rep)
            assert r_send.status_code == 200
            assert r_send.json()["status"] == QuotationStatus.SENT_TO_CUSTOMER.value

            # 4. Customer views portal quotation list & details
            r_port_list = await client.get("/api/v1/portal/quotations", headers=headers_cust)
            assert r_port_list.status_code == 200
            assert len(r_port_list.json()) == 1

            r_port_quote = await client.get(f"/api/v1/portal/quotations/{quote_id}", headers=headers_cust)
            assert r_port_quote.status_code == 200
            assert r_port_quote.json()["quote_number"] == r_create.json()["quote_number"]

            # 5. Customer submits message & counter-offer
            r_msg = await client.post(
                f"/api/v1/portal/quotations/{quote_id}/messages",
                json={"message": "Is a 5% order discount possible?"},
                headers=headers_cust,
            )
            assert r_msg.status_code == 201

            r_counter = await client.post(
                f"/api/v1/portal/quotations/{quote_id}/counter-offer",
                json={
                    "request_type": "COUNTER_OFFER",
                    "requested_order_discount_pct": 5.00,
                    "message": "Offering 5% order discount.",
                },
                headers=headers_cust,
            )
            assert r_counter.status_code == 201
            req_id = r_counter.json()["id"]

            # 6. Sales Rep views inbox & accepts counter-offer
            r_inbox = await client.get(f"/api/v1/quotations/{quote_id}/negotiation-inbox", headers=headers_rep)
            assert r_inbox.status_code == 200
            assert len(r_inbox.json()) == 1

            r_accept = await client.post(
                f"/api/v1/quotations/{quote_id}/negotiation-requests/{req_id}/accept",
                headers=headers_rep,
            )
            assert r_accept.status_code == 200
            assert r_accept.json()["status"] in {QuotationStatus.SENT_TO_CUSTOMER.value, QuotationStatus.APPROVED.value}

            # 7. Customer confirms quotation
            r_confirm = await client.post(f"/api/v1/portal/quotations/{quote_id}/confirm", headers=headers_cust)
            assert r_confirm.status_code == 200
            assert r_confirm.json()["status"] == QuotationStatus.CUSTOMER_ACCEPTED.value

            # 8. Check notification inbox for Sales Rep
            r_notif = await client.get("/api/v1/notifications", headers=headers_rep)
            assert r_notif.status_code == 200
            notifs = r_notif.json()
            assert len(notifs) >= 1
    finally:
        app.dependency_overrides.clear()
