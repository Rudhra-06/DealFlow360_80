import pytest
from decimal import Decimal
from sqlalchemy import select

from app.core.enums import QuotationStatus
from app.core.roles import RoleName
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.quotation import Quotation
from app.models.quotation_line import QuoteLine
from app.models.role import Role
from app.models.user import User
from app.services.billing import BillingService
from app.services.exceptions import OverpaymentError
from app.services.order import OrderService
from app.services.payment import PaymentService
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
async def test_payment_recording_and_invoice_balance_update(db_session):
    role_admin = await get_or_create_role(db_session, RoleName.ADMIN)
    role_rep = await get_or_create_role(db_session, RoleName.SALES_REP)
    tier = CustomerTier(name="Pay Tier")
    cat = ProductCategory(name="Pay Cat")
    db_session.add_all([tier, cat])
    await db_session.flush()

    admin = User(email="admin_pay@example.com", hashed_password="pw", full_name="Admin Pay", role_id=role_admin.id)
    rep = User(email="rep_pay@example.com", hashed_password="pw", full_name="Rep Pay", role_id=role_rep.id)
    cust = Customer(customer_code="PAY-CUST-1", name="Pay Corp", email="pay@corp.com", tier_id=tier.id)
    db_session.add_all([admin, rep, cust])
    await db_session.flush()

    prod = Product(sku="PAY-P1", name="Pay Prod", category_id=cat.id, list_price=Decimal("1000.00"), cost_price=Decimal("500.00"))
    db_session.add(prod)
    await db_session.flush()

    quote = Quotation(
        quote_number="Q-PAY-1",
        customer_id=cust.id,
        sales_rep_id=rep.id,
        currency="USD",
        payment_terms_days=30,
        status=QuotationStatus.CUSTOMER_CONFIRMED.value,
        gross_subtotal=Decimal("1000.00"),
        net_total=Decimal("1000.00"),
        total_cost=Decimal("500.00"),
        margin_amount=Decimal("500.00"),
        margin_pct=Decimal("50.00"),
    )
    db_session.add(quote)
    await db_session.flush()

    line = QuoteLine(
        quotation_id=quote.id,
        product_id=prod.id,
        quantity=Decimal("1"),
        unit_list_price=Decimal("1000.00"),
        unit_cost=Decimal("500.00"),
        gross_line_total=Decimal("1000.00"),
        net_line_total=Decimal("1000.00"),
        line_cost=Decimal("500.00"),
        margin_amount=Decimal("500.00"),
        margin_pct=Decimal("50.00"),
    )
    db_session.add(line)
    await db_session.flush()

    v_service = QuoteVersionService(db_session)
    v1 = await v_service.create_version_snapshot(quote.id, "INITIAL_RELEASE", rep.id)
    quote.confirmed_quote_version_id = v1.id
    await db_session.commit()

    order_service = OrderService(db_session)
    order = await order_service.create_order_from_confirmed_quotation(quote.id, rep.id)

    billing_service = BillingService(db_session)
    invoices = await billing_service.initialize_order_billing(order.id, admin.id)
    inv = invoices[0]

    assert inv.balance_due == Decimal("1000.00")
    assert inv.status == "ISSUED"

    payment_service = PaymentService(db_session)

    # Test overpayment rejection
    with pytest.raises(OverpaymentError):
        await payment_service.record_payment(
            customer_id=cust.id,
            amount=1500.0,
            currency="USD",
            payment_method="BANK_TRANSFER",
            allocations_input=[{"invoice_id": inv.id, "amount": 1500.0}],
            recorded_by_user_id=admin.id,
        )

    # Test valid full payment
    payment = await payment_service.record_payment(
        customer_id=cust.id,
        amount=1000.0,
        currency="USD",
        payment_method="BANK_TRANSFER",
        allocations_input=[{"invoice_id": inv.id, "amount": 1000.0}],
        recorded_by_user_id=admin.id,
        reference="REF-WIRE-999",
    )

    assert payment.id is not None
    assert payment.amount == Decimal("1000.00")

    updated_inv = await billing_service.invoice_repo.get_by_id(db_session, inv.id)
    assert updated_inv.paid_amount == Decimal("1000.00")
    assert updated_inv.balance_due == Decimal("0.00")
    assert updated_inv.status == "PAID"

    updated_order = await order_service.order_repo.get_by_id(db_session, order.id)
    assert updated_order.status == "PAID"
