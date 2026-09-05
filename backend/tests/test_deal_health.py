from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.enums import QuotationStatus, RoleName
from app.core.security import hash_password
from app.engines.deal_health import DealHealthConfigData, DealHealthContext, DealHealthEngine
from app.main import app
from app.db.session import get_db
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.deal_alert import DealAlert
from app.models.deal_health_config import DealHealthConfig
from app.models.deal_health_snapshot import DealHealthSnapshot
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.quotation import Quotation
from app.models.quotation_line import QuoteLine
from app.models.quote_approval_step import QuoteApprovalStep
from app.models.quote_negotiation_message import QuoteNegotiationMessage
from app.models.role import Role
from app.models.user import User
from app.services.deal_action import DealActionService
from app.services.deal_alert import DealAlertService
from app.services.deal_health import DealHealthService
from app.services.quote_version import QuoteVersionService


async def get_or_create_role(db, name):
    res = await db.execute(select(Role).where(Role.name == name))
    r = res.scalar_one_or_none()
    if not r:
        r = Role(name=name, description=name)
        db.add(r)
        await db.flush()
    return r


@pytest.mark.asyncio
async def test_deal_health_engine_pure_healthy():
    ctx = DealHealthContext(
        quotation_id=1,
        quote_number="Q-HEALTHY-1",
        status="SENT_TO_CUSTOMER",
        sales_rep_id=10,
        customer_id=20,
        net_total=Decimal("1000.00"),
        margin_pct=Decimal("50.00"),
        weighted_effective_discount_pct=Decimal("5.00"),
        last_meaningful_activity_at=datetime.now(timezone.utc) - timedelta(days=1),
        sales_rep_historical_discounts=[Decimal("5.00"), Decimal("6.00"), Decimal("4.00")],
    )
    config = DealHealthConfigData()

    eval_result = DealHealthEngine.evaluate(ctx, config)
    assert eval_result.health_score == Decimal("100.00")
    assert eval_result.health_level == "HEALTHY"
    assert len(eval_result.signals) == 0
    assert "HEALTHY" in eval_result.summary


@pytest.mark.asyncio
async def test_deal_health_engine_stalled_and_anomaly():
    now = datetime.now(timezone.utc)
    ctx = DealHealthContext(
        quotation_id=2,
        quote_number="Q-STALLED-1",
        status="UNDER_NEGOTIATION",
        sales_rep_id=10,
        customer_id=20,
        net_total=Decimal("5000.00"),
        margin_pct=Decimal("40.00"),
        weighted_effective_discount_pct=Decimal("20.00"),
        last_meaningful_activity_at=now - timedelta(days=7),
        last_negotiation_activity_at=now - timedelta(days=4),
        sales_rep_historical_discounts=[Decimal("5.00"), Decimal("7.00"), Decimal("9.00")],
    )
    config = DealHealthConfigData(stalled_quote_days=5, negotiation_stall_days=3, discount_anomaly_threshold_pct=Decimal("10.00"))

    eval_result = DealHealthEngine.evaluate(ctx, config, as_of=now)
    assert len(eval_result.signals) == 3
    sig_types = {s.signal_type for s in eval_result.signals}
    assert "STALLED_QUOTE" in sig_types
    assert "DISCOUNT_ANOMALY" in sig_types
    assert "NEGOTIATION_STALL" in sig_types
    assert eval_result.health_level in {"WATCH", "AT_RISK", "CRITICAL"}


@pytest.mark.asyncio
async def test_deal_health_engine_insufficient_sample_size():
    now = datetime.now(timezone.utc)
    ctx = DealHealthContext(
        quotation_id=3,
        quote_number="Q-INSUFFICIENT-1",
        status="SENT_TO_CUSTOMER",
        sales_rep_id=10,
        customer_id=20,
        net_total=Decimal("2000.00"),
        margin_pct=Decimal("30.00"),
        weighted_effective_discount_pct=Decimal("25.00"),
        last_meaningful_activity_at=now - timedelta(days=1),
        sales_rep_historical_discounts=[Decimal("5.00")],  # Only 1 sample (< 3)
    )
    config = DealHealthConfigData(discount_anomaly_threshold_pct=Decimal("10.00"))

    eval_result = DealHealthEngine.evaluate(ctx, config, as_of=now)
    sig_types = {s.signal_type for s in eval_result.signals}
    assert "DISCOUNT_ANOMALY" not in sig_types


@pytest.mark.asyncio
async def test_deal_health_service_evaluation_and_deduplication(db_session):
    role_rep = await get_or_create_role(db_session, RoleName.SALES_REP)
    tier = CustomerTier(name="Health Tier")
    cat = ProductCategory(name="Health Cat")
    db_session.add_all([tier, cat])
    await db_session.flush()

    rep = User(email="dh_rep@example.com", hashed_password="pw", full_name="DH Rep", role_id=role_rep.id)
    cust = Customer(customer_code="DH-CUST-1", name="DH Corp", email="dh@corp.com", tier_id=tier.id)
    db_session.add_all([rep, cust])
    await db_session.flush()

    prod = Product(sku="DH-P1", name="DH Prod", category_id=cat.id, list_price=Decimal("100.00"), cost_price=Decimal("50.00"))
    db_session.add(prod)
    await db_session.flush()

    quote = Quotation(
        quote_number="Q-DH-100",
        customer_id=cust.id,
        sales_rep_id=rep.id,
        currency="USD",
        payment_terms_days=30,
        status=QuotationStatus.SENT_TO_CUSTOMER.value,
        gross_subtotal=Decimal("100.00"),
        net_total=Decimal("100.00"),
        total_cost=Decimal("50.00"),
        margin_amount=Decimal("50.00"),
        margin_pct=Decimal("50.00"),
        updated_at=datetime.now(timezone.utc) - timedelta(days=10),
    )
    db_session.add(quote)
    await db_session.flush()

    service = DealHealthService(db_session)
    # Evaluate 1st time -> Stalled quote alert created
    snap1 = await service.evaluate_quotation_health(quote.id)
    assert snap1.id is not None
    assert snap1.signal_count >= 1

    alerts1 = await service.alert_repo.list_alerts(db_session, quotation_id=quote.id)
    assert len(alerts1) == 1
    assert alerts1[0].occurrence_count == 1

    # Evaluate 2nd time -> Deduplication: updates occurrence_count to 2
    snap2 = await service.evaluate_quotation_health(quote.id)
    alerts2 = await service.alert_repo.list_alerts(db_session, quotation_id=quote.id)
    assert len(alerts2) == 1
    assert alerts2[0].occurrence_count == 2


@pytest.mark.asyncio
async def test_alert_lifecycle_acknowledge_resolve_nudge(db_session):
    role_rep = await get_or_create_role(db_session, RoleName.SALES_REP)
    role_mgr = await get_or_create_role(db_session, RoleName.SALES_MANAGER)
    tier = CustomerTier(name="Alert Tier")
    cat = ProductCategory(name="Alert Cat")
    db_session.add_all([tier, cat])
    await db_session.flush()

    rep = User(email="alert_rep@example.com", hashed_password="pw", full_name="Alert Rep", role_id=role_rep.id)
    mgr = User(email="alert_mgr@example.com", hashed_password="pw", full_name="Alert Mgr", role_id=role_mgr.id)
    cust = Customer(customer_code="ALT-CUST-1", name="Alert Corp", email="alt@corp.com", tier_id=tier.id)
    db_session.add_all([rep, mgr, cust])
    await db_session.flush()

    quote = Quotation(
        quote_number="Q-ALT-200",
        customer_id=cust.id,
        sales_rep_id=rep.id,
        currency="USD",
        payment_terms_days=30,
        status=QuotationStatus.SENT_TO_CUSTOMER.value,
        gross_subtotal=Decimal("500.00"),
        net_total=Decimal("500.00"),
        total_cost=Decimal("200.00"),
        margin_amount=Decimal("300.00"),
        margin_pct=Decimal("60.00"),
        updated_at=datetime.now(timezone.utc) - timedelta(days=10),
    )
    db_session.add(quote)
    await db_session.flush()

    dh_service = DealHealthService(db_session)
    await dh_service.evaluate_quotation_health(quote.id)

    alert_service = DealAlertService(db_session)
    alerts = await alert_service.list_alerts(quotation_id=quote.id)
    assert len(alerts) >= 1
    alert_id = alerts[0].id

    # 1. Acknowledge
    ack_alert = await alert_service.acknowledge_alert(alert_id, rep)
    assert ack_alert.status == "ACKNOWLEDGED"

    # 2. Trigger Nudge
    action_service = DealActionService(db_session)
    action = await action_service.trigger_nudge(alert_id, "NUDGE_SALES_REP", "Please check this stalled deal.", mgr)
    assert action.id is not None
    assert action.action_type == "NUDGE_SALES_REP"

    # 3. Resolve
    res_alert = await alert_service.resolve_alert(alert_id, "Customer contacted and agreed to call.", mgr)
    assert res_alert.status == "RESOLVED"


@pytest.mark.asyncio
async def test_customer_role_security_isolation(db_session):
    role_cust = await get_or_create_role(db_session, RoleName.CUSTOMER)
    pass_hash = hash_password("password123")
    user_cust = User(email="cust_dh_sec@example.com", hashed_password=pass_hash, full_name="Cust Sec", role_id=role_cust.id)
    db_session.add(user_cust)
    await db_session.commit()

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res_login = await client.post("/api/v1/auth/login", json={"email": "cust_dh_sec@example.com", "password": "password123"})
            token = res_login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            r1 = await client.get("/api/v1/deal-health", headers=headers)
            assert r1.status_code == 403

            r2 = await client.get("/api/v1/deal-alerts", headers=headers)
            assert r2.status_code == 403

            r3 = await client.get("/api/v1/deal-health-config", headers=headers)
            assert r3.status_code == 403
    finally:
        app.dependency_overrides.clear()
