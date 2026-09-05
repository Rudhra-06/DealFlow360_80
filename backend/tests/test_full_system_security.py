"""Security & Data Leak Audit Integration Tests for Phase 6 Part 3."""

import pytest
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import RoleName
from app.models.user import User
from app.models.customer import Customer
from app.models.quotation import Quotation
from app.schemas.portal import PortalQuotationDetail
from app.services.portal_quotation import PortalQuotationService
from app.services.customer_360 import Customer360Service
from tests.conftest import get_or_create_role


@pytest.mark.asyncio
async def test_customer_portal_data_leak_prevention(db_session: AsyncSession):
    role_cust = await get_or_create_role(db_session, RoleName.CUSTOMER)
    cust_user = User(email="sec_cust@test.com", password_hash="hash", full_name="Sec Cust", is_active=True)
    cust_user.roles.append(role_cust)
    db_session.add(cust_user)
    await db_session.flush()

    cust = Customer(customer_code="CUST-SEC-01", company_name="Sec Corp")
    db_session.add(cust)
    await db_session.flush()

    quote = Quotation(
        quotation_number="QT-SEC-001",
        customer_id=cust.id,
        status="SENT_TO_CUSTOMER",
        currency="USD",
        net_total=Decimal("5000.00"),
        margin_pct=Decimal("45.00"),  # Sensitive internal field!
        blended_risk_score=Decimal("85.00"),  # Sensitive internal field!
    )
    db_session.add(quote)
    await db_session.commit()

    portal_service = PortalQuotationService(db_session)
    portal_dto = await portal_service.get_portal_quotation(quote.id, cust_user)

    # Convert to Pydantic schema
    detail_schema = PortalQuotationDetail.model_validate(portal_dto)
    schema_dict = detail_schema.model_dump()

    # Verify internal sensitive fields are strictly excluded from portal schema
    assert "margin_pct" not in schema_dict
    assert "blended_risk_score" not in schema_dict
    assert "unit_cost" not in schema_dict


@pytest.mark.asyncio
async def test_customer_360_forbidden_for_customer_role(db_session: AsyncSession):
    role_cust = await get_or_create_role(db_session, RoleName.CUSTOMER)
    cust_user = User(email="sec_cust_360@test.com", password_hash="hash", full_name="Sec Cust 360", is_active=True)
    cust_user.roles.append(role_cust)
    db_session.add(cust_user)
    await db_session.flush()

    cust = Customer(customer_code="CUST-SEC-02", company_name="Sec 360 Corp")
    db_session.add(cust)
    await db_session.commit()

    service = Customer360Service(db_session)

    # Customer 360 is internal intelligence only; CUSTOMER role is blocked
    with pytest.raises(HTTPException) as exc_info:
        await service.get_customer_360(cust.id, cust_user)
    assert exc_info.value.status_code == 403
