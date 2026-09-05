import pytest
from decimal import Decimal
from sqlalchemy import select

from app.core.enums import QuotationStatus
from app.core.roles import RoleName
from app.models.approval_policy import ApprovalPolicy
from app.models.customer import Customer
from app.models.customer_portal_access import CustomerPortalAccess
from app.models.customer_tier import CustomerTier
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.quotation import Quotation
from app.models.quotation_line import QuoteLine
from app.models.role import Role
from app.models.user import User
from app.schemas.quote_negotiation import QuoteNegotiationRequestCreate
from app.services.quote_approval import QuoteApprovalService
from app.services.quote_negotiation import QuoteNegotiationService
from app.services.quote_version import QuoteVersionService


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
async def test_reapproval_flow_on_negotiation_accept(db_session):
    role_cust = await get_or_create_role(db_session, RoleName.CUSTOMER)
    role_rep = await get_or_create_role(db_session, RoleName.SALES_REP)
    role_mgr = await get_or_create_role(db_session, RoleName.SALES_MANAGER)
    tier = await get_or_create_tier(db_session)
    cat = await get_or_create_category(db_session)

    user_cust = User(email="cust_reapp@example.com", hashed_password="pw", full_name="Cust Reapp", role_id=role_cust.id)
    user_rep = User(email="rep_reapp@example.com", hashed_password="pw", full_name="Rep Reapp", role_id=role_rep.id)
    user_mgr = User(email="mgr_reapp@example.com", hashed_password="pw", full_name="Mgr Reapp", role_id=role_mgr.id)
    customer = Customer(customer_code="CUST-REAPP-1", name="Reapp Corp", email="r@corp.com", tier_id=tier.id)
    db_session.add_all([user_cust, user_rep, user_mgr, customer])
    await db_session.flush()

    access = CustomerPortalAccess(user_id=user_cust.id, customer_id=customer.id, is_active=True)
    db_session.add(access)

    # Active Policy: Discount above 10% requires Manager Approval
    policy = ApprovalPolicy(
        name="High Discount Policy",
        discount_above_pct=Decimal("10.00"),
        approval_role=RoleName.SALES_MANAGER,
        priority=100,
        is_active=True,
    )
    db_session.add(policy)

    prod = Product(sku="REAPP-1", name="Reapp Product", category_id=cat.id, list_price=Decimal("1000.00"), cost_price=Decimal("400.00"))
    db_session.add(prod)
    await db_session.flush()

    quote = Quotation(
        quote_number="Q-REAPP-001",
        customer_id=customer.id,
        sales_rep_id=user_rep.id,
        currency="USD",
        payment_terms_days=30,
        order_discount_pct=Decimal("0.00"),
        status=QuotationStatus.SENT_TO_CUSTOMER.value,
        gross_subtotal=Decimal("1000.00"),
        discount_amount=Decimal("0.00"),
        net_total=Decimal("1000.00"),
        total_cost=Decimal("400.00"),
        margin_amount=Decimal("600.00"),
        margin_pct=Decimal("60.00"),
        weighted_effective_discount_pct=Decimal("0.00"),
        blended_risk_score=Decimal("5.00"),
        risk_level="GREEN",
    )
    db_session.add(quote)
    await db_session.flush()

    line = QuoteLine(
        quotation_id=quote.id,
        product_id=prod.id,
        quantity=Decimal("1"),
        unit_list_price=Decimal("1000.00"),
        unit_cost=Decimal("400.00"),
        line_discount_pct=Decimal("0.00"),
        effective_discount_pct=Decimal("0.00"),
        gross_line_total=Decimal("1000.00"),
        discount_amount=Decimal("0.00"),
        net_line_total=Decimal("1000.00"),
        line_cost=Decimal("400.00"),
        margin_amount=Decimal("600.00"),
        margin_pct=Decimal("60.00"),
        risk_level="GREEN",
    )
    db_session.add(line)
    await db_session.commit()

    v_service = QuoteVersionService(db_session)
    v1 = await v_service.create_version_snapshot(quote.id, "INITIAL_RELEASE", user_rep.id)
    quote.current_version_id = v1.id
    await db_session.commit()

    neg_service = QuoteNegotiationService(db_session)

    # Customer submits counter-offer requesting 15% discount (exceeds 10% policy limit!)
    req = await neg_service.submit_counter_offer(
        quote.id,
        QuoteNegotiationRequestCreate(
            request_type="COUNTER_OFFER",
            requested_order_discount_pct=Decimal("15.00"),
            message="We request 15% discount for bulk commitment.",
        ),
        user_cust,
    )

    # Sales Rep accepts negotiation request -> triggers reapproval engine
    updated_quote = await neg_service.accept_negotiation_request(quote.id, req.id, user_rep)

    assert updated_quote.status in {
        QuotationStatus.PENDING_MANAGER_APPROVAL.value,
        QuotationStatus.REAPPROVAL_REQUIRED.value,
    }

    # Fetch created approval step
    approval_service = QuoteApprovalService(db_session)
    steps = await approval_service.list_approval_steps(quote.id)
    assert len(steps) >= 1
    step = steps[-1]
    assert step.approval_role == RoleName.SALES_MANAGER
    assert step.approval_context == "NEGOTIATION"

    # Manager approves step
    final_quote = await approval_service.process_decision(
        quotation_id=quote.id,
        step_id=step.id,
        action="APPROVE",
        reason="Approved bulk discount",
        current_user=user_mgr,
    )

    # Should transition back to SENT_TO_CUSTOMER for customer confirmation!
    assert final_quote.status == QuotationStatus.SENT_TO_CUSTOMER.value
