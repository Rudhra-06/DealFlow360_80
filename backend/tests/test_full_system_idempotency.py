"""Idempotency Integration Tests for Phase 6 Part 3."""

import pytest
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import RoleName
from app.models.user import User
from app.models.customer import Customer
from app.models.quotation import Quotation
from app.models.sales_order import SalesOrder
from app.models.deal_health_config import DealHealthConfig
from app.models.deal_alert import DealAlert
from app.services.portal_quotation import PortalQuotationService
from app.services.deal_health import DealHealthService
from tests.conftest import get_or_create_role


@pytest.mark.asyncio
async def test_duplicate_customer_confirmation_idempotency(db_session: AsyncSession):
    role_cust = await get_or_create_role(db_session, RoleName.CUSTOMER)
    cust_user = User(email="idem_cust@test.com", password_hash="hash", full_name="Idem Cust", is_active=True)
    cust_user.roles.append(role_cust)
    db_session.add(cust_user)
    await db_session.flush()

    cust = Customer(customer_code="CUST-IDEM-01", company_name="Idem Corp")
    db_session.add(cust)
    await db_session.flush()

    quote = Quotation(quotation_number="QT-IDEM-001", customer_id=cust.id, status="SENT_TO_CUSTOMER", currency="USD", net_total=Decimal("1200.00"))
    db_session.add(quote)
    await db_session.commit()

    portal_service = PortalQuotationService(db_session)

    # First confirmation
    so1 = await portal_service.confirm_quotation(quote.id, actor_user_id=cust_user.id)
    await db_session.commit()

    # Second confirmation retry
    so2 = await portal_service.confirm_quotation(quote.id, actor_user_id=cust_user.id)
    await db_session.commit()

    assert so1.id == so2.id

    so_cnt = (await db_session.execute(select(func.count(SalesOrder.id)).where(SalesOrder.quotation_id == quote.id))).scalar()
    assert so_cnt == 1


@pytest.mark.asyncio
async def test_repeated_health_evaluation_alert_deduplication(db_session: AsyncSession):
    cust = Customer(customer_code="CUST-IDEM-02", company_name="Health Idem Corp")
    db_session.add(cust)
    await db_session.flush()

    # Stalled quote (updated_at set to 10 days ago)
    stale_date = datetime.now(timezone.utc) - timedelta(days=10)
    quote = Quotation(quotation_number="QT-IDEM-HEALTH", customer_id=cust.id, status="UNDER_NEGOTIATION", currency="USD", net_total=Decimal("3000.00"), updated_at=stale_date)
    dhc = DealHealthConfig(name="Idem Health Config", is_active=True, stalled_quote_days=5)
    db_session.add_all([quote, dhc])
    await db_session.commit()

    from datetime import datetime, timezone, timedelta
    service = DealHealthService(db_session)

    # First evaluation
    eval1 = await service.evaluate_quotation_health(quote.id)
    await db_session.commit()

    # Second evaluation
    eval2 = await service.evaluate_quotation_health(quote.id)
    await db_session.commit()

    # Verify active alerts count is 1 (deduplicated)
    alerts_stmt = select(DealAlert).where(DealAlert.quotation_id == quote.id, DealAlert.status.in_(["OPEN", "ACKNOWLEDGED"]))
    alerts = (await db_session.execute(alerts_stmt)).scalars().all()
    assert len(alerts) == 1
    assert alerts[0].occurrence_count >= 2
