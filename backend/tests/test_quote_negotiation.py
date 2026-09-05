import pytest
from decimal import Decimal
from sqlalchemy import select

from app.core.enums import QuotationStatus
from app.core.roles import RoleName
from app.models.customer import Customer
from app.models.customer_portal_access import CustomerPortalAccess
from app.models.customer_tier import CustomerTier
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.quotation import Quotation
from app.models.quotation_line import QuoteLine
from app.models.role import Role
from app.models.user import User
from app.schemas.quote_negotiation import (
    QuoteNegotiationLineChangeCreate,
    QuoteNegotiationMessageCreate,
    QuoteNegotiationRequestCreate,
    QuoteNegotiationRequestReject,
)
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
async def test_quote_negotiation_messaging_and_counter_offer(db_session):
    role_cust = await get_or_create_role(db_session, RoleName.CUSTOMER)
    role_rep = await get_or_create_role(db_session, RoleName.SALES_REP)
    tier = await get_or_create_tier(db_session)
    cat = await get_or_create_category(db_session)

    user_cust = User(email="cust_neg@example.com", hashed_password="pw", full_name="Cust Neg", role_id=role_cust.id)
    user_rep = User(email="rep_neg@example.com", hashed_password="pw", full_name="Rep Neg", role_id=role_rep.id)
    customer = Customer(customer_code="CUST-NEG-1", name="Negot Corp", email="n@corp.com", tier_id=tier.id)
    db_session.add_all([user_cust, user_rep, customer])
    await db_session.flush()

    access = CustomerPortalAccess(user_id=user_cust.id, customer_id=customer.id, is_active=True)
    db_session.add(access)

    prod = Product(sku="NEG-1", name="Neg Product", category_id=cat.id, list_price=Decimal("500.00"), cost_price=Decimal("200.00"))
    db_session.add(prod)
    await db_session.flush()

    quote = Quotation(
        quote_number="Q-NEG-001",
        customer_id=customer.id,
        sales_rep_id=user_rep.id,
        currency="USD",
        payment_terms_days=30,
        order_discount_pct=Decimal("0.00"),
        status=QuotationStatus.SENT_TO_CUSTOMER.value,
        gross_subtotal=Decimal("500.00"),
        discount_amount=Decimal("0.00"),
        net_total=Decimal("500.00"),
        total_cost=Decimal("200.00"),
        margin_amount=Decimal("300.00"),
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
        unit_list_price=Decimal("500.00"),
        unit_cost=Decimal("200.00"),
        line_discount_pct=Decimal("0.00"),
        effective_discount_pct=Decimal("0.00"),
        gross_line_total=Decimal("500.00"),
        discount_amount=Decimal("0.00"),
        net_line_total=Decimal("500.00"),
        line_cost=Decimal("200.00"),
        margin_amount=Decimal("300.00"),
        margin_pct=Decimal("60.00"),
        risk_level="GREEN",
    )
    db_session.add(line)
    await db_session.commit()

    # Create v1 initial version
    v_service = QuoteVersionService(db_session)
    v1 = await v_service.create_version_snapshot(quote.id, "INITIAL_RELEASE", user_rep.id)
    quote.current_version_id = v1.id
    await db_session.commit()

    neg_service = QuoteNegotiationService(db_session)

    # 1. Customer posts message
    msg = await neg_service.add_customer_message(
        quote.id,
        QuoteNegotiationMessageCreate(message="Can we get a 5% discount on order?", quotation_line_id=line.id),
        user_cust,
    )
    assert msg.message == "Can we get a 5% discount on order?"
    assert msg.is_customer_visible is True

    # Check status transitioned to UNDER_NEGOTIATION
    quote_ref = await neg_service.quote_repo.get_by_id(db_session, quote.id)
    assert quote_ref.status == QuotationStatus.UNDER_NEGOTIATION.value

    # 2. Sales Rep posts internal reply
    reply = await neg_service.add_internal_message(
        quote.id,
        QuoteNegotiationMessageCreate(message="Please submit a formal counter-offer via portal."),
        user_rep,
    )
    assert reply.author_user_id == user_rep.id

    # 3. Customer submits counter offer
    req = await neg_service.submit_counter_offer(
        quote.id,
        QuoteNegotiationRequestCreate(
            request_type="COUNTER_OFFER",
            requested_order_discount_pct=Decimal("5.00"),
            requested_payment_terms_days=45,
            message="Requesting 5% discount and 45 days payment terms.",
            line_changes=[
                QuoteNegotiationLineChangeCreate(quotation_line_id=line.id, requested_line_discount_pct=Decimal("5.00"))
            ],
        ),
        user_cust,
    )
    assert req.status == "PENDING"
    assert req.requested_order_discount_pct == Decimal("5.00")

    # 4. Sales Rep rejects counter-offer
    rejected_req = await neg_service.reject_negotiation_request(
        quote.id, req.id, QuoteNegotiationRequestReject(rejection_reason="Margin is too low"), user_rep
    )
    assert rejected_req.status == "REJECTED"
    assert rejected_req.rejection_reason == "Margin is too low"
