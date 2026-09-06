"""Report Export Tests for Phase 6 Part 2 & Entity PDF Exports."""

import pytest
import io
import openpyxl
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import RoleName
from app.models.user import User
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.quotation import Quotation
from app.models.quotation_line import QuoteLine
from app.models.sales_order import SalesOrder
from app.models.invoice import Invoice
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.customer_portal_access import CustomerPortalAccess
from app.schemas.reports import ReportExportRequest, ReportExportFormat, ReportTypeEnum
from app.reports.pdf_renderer import PDFReportRenderer
from app.reports.xlsx_renderer import XLSXReportRenderer, sanitize_xlsx_value
from app.services.report_export import ReportExportService
from tests.conftest import get_or_create_role


def test_pdf_renderer():
    data = {
        "quotation_count": 10,
        "confirmed_order_value": {"USD": Decimal("15000.00"), "EUR": Decimal("8000.00")},
        "confirmation_rate": Decimal("40.00"),
    }
    pdf_bytes = PDFReportRenderer.render_report("EXECUTIVE_SUMMARY", data, "Executive Summary")
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")


def test_xlsx_renderer_and_formula_injection_protection():
    assert sanitize_xlsx_value("=SUM(A1:A10)") == "'=SUM(A1:A10)"
    assert sanitize_xlsx_value("+12345") == "'+12345"
    assert sanitize_xlsx_value("Normal Text") == "Normal Text"

    data = {
        "quotation_count": 5,
        "confirmed_order_value": {"USD": Decimal("12000.00")},
        "reps": [
            {"rep_name": "=MALICIOUS()", "quotes_created": 3, "quotes_confirmed": 2}
        ]
    }
    xlsx_bytes = XLSXReportRenderer.render_report("SALES_PERFORMANCE", data, "Sales Performance")
    assert isinstance(xlsx_bytes, bytes)

    wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes))
    assert "Summary" in wb.sheetnames


@pytest.mark.asyncio
async def test_report_export_service_and_audit(db_session: AsyncSession):
    role_admin = await get_or_create_role(db_session, RoleName.ADMIN)
    user = User(email=f"report_admin_{uuid.uuid4().hex[:6]}@test.com", hashed_password="hash", full_name="Report Admin", role_id=role_admin.id, is_active=True)
    db_session.add(user)
    await db_session.commit()

    req = ReportExportRequest(
        report_type=ReportTypeEnum.EXECUTIVE_SUMMARY,
        format=ReportExportFormat.PDF,
    )
    service = ReportExportService(db_session)
    file_bytes, filename, mime_type = await service.export_report(req, user)

    assert isinstance(file_bytes, bytes)
    assert file_bytes.startswith(b"%PDF")
    assert filename.endswith(".pdf")
    assert mime_type == "application/pdf"


@pytest.mark.asyncio
async def test_customer_role_export_internal_403(db_session: AsyncSession):
    role_cust = await get_or_create_role(db_session, RoleName.CUSTOMER)
    cust_user = User(email=f"cust_user_{uuid.uuid4().hex[:6]}@test.com", hashed_password="hash", full_name="Cust User", role_id=role_cust.id, is_active=True)
    db_session.add(cust_user)
    await db_session.commit()

    req = ReportExportRequest(
        report_type=ReportTypeEnum.EXECUTIVE_SUMMARY,
        format=ReportExportFormat.XLSX,
    )
    service = ReportExportService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await service.export_report(req, cust_user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_quotation_pdf_export_entity_scoped(db_session: AsyncSession):
    role_admin = await get_or_create_role(db_session, RoleName.ADMIN)
    admin_user = User(email=f"admin_q_{uuid.uuid4().hex[:6]}@test.com", hashed_password="hash", full_name="Admin Q", role_id=role_admin.id, is_active=True)
    db_session.add(admin_user)
    await db_session.flush()

    tier = CustomerTier(name=f"Tier-{uuid.uuid4().hex[:4]}")
    db_session.add(tier)
    await db_session.flush()

    cust_a = Customer(customer_code=f"CUST-{uuid.uuid4().hex[:4]}", name="Alpha Alpha Corp", tier_id=tier.id, is_active=True)
    db_session.add(cust_a)
    await db_session.flush()

    cat = ProductCategory(name=f"Cat-{uuid.uuid4().hex[:4]}")
    db_session.add(cat)
    await db_session.flush()

    prod_a = Product(sku=f"SKU-A-{uuid.uuid4().hex[:4]}", name="Alpha Software Suite", list_price=Decimal("1500.00"), cost_price=Decimal("800.00"), category_id=cat.id)
    prod_b = Product(sku=f"SKU-B-{uuid.uuid4().hex[:4]}", name="Beta Cloud Module", list_price=Decimal("3000.00"), cost_price=Decimal("1500.00"), category_id=cat.id)
    db_session.add_all([prod_a, prod_b])
    await db_session.flush()

    quote_a = Quotation(
        quote_number=f"Q-TEST-A-{uuid.uuid4().hex[:4]}",
        customer_id=cust_a.id,
        sales_rep_id=admin_user.id,
        status="APPROVED",
        gross_subtotal=Decimal("1500.00"),
        net_total=Decimal("1500.00"),
        currency="USD",
    )
    db_session.add(quote_a)
    await db_session.flush()

    line_a = QuoteLine(quotation_id=quote_a.id, product_id=prod_a.id, quantity=1, unit_list_price=Decimal("1500.00"), unit_cost=Decimal("800.00"), line_discount_pct=Decimal("0.00"), net_line_total=Decimal("1500.00"), gross_line_total=Decimal("1500.00"))
    db_session.add(line_a)

    cust_b = Customer(customer_code=f"CUST-{uuid.uuid4().hex[:4]}", name="Omega Beta Systems", tier_id=tier.id, is_active=True)
    db_session.add(cust_b)
    await db_session.flush()

    quote_b = Quotation(
        quote_number=f"Q-TEST-B-{uuid.uuid4().hex[:4]}",
        customer_id=cust_b.id,
        sales_rep_id=admin_user.id,
        status="SENT_TO_CUSTOMER",
        gross_subtotal=Decimal("9000.00"),
        net_total=Decimal("9000.00"),
        currency="EUR",
    )
    db_session.add(quote_b)
    await db_session.flush()

    line_b = QuoteLine(quotation_id=quote_b.id, product_id=prod_b.id, quantity=3, unit_list_price=Decimal("3000.00"), unit_cost=Decimal("1500.00"), line_discount_pct=Decimal("0.00"), net_line_total=Decimal("9000.00"), gross_line_total=Decimal("9000.00"))
    db_session.add(line_b)
    await db_session.commit()

    service = ReportExportService(db_session)

    req_a = ReportExportRequest(report_type=ReportTypeEnum.QUOTATION, format=ReportExportFormat.PDF, quotation_id=quote_a.id)
    pdf_a, filename_a, _ = await service.export_report(req_a, admin_user)

    req_b = ReportExportRequest(report_type=ReportTypeEnum.QUOTATION, format=ReportExportFormat.PDF, quotation_id=quote_b.id)
    pdf_b, filename_b, _ = await service.export_report(req_b, admin_user)

    assert isinstance(pdf_a, bytes) and pdf_a.startswith(b"%PDF")
    assert isinstance(pdf_b, bytes) and pdf_b.startswith(b"%PDF")
    assert quote_a.quote_number in filename_a
    assert quote_b.quote_number in filename_b
    assert pdf_a != pdf_b


@pytest.mark.asyncio
async def test_customer_360_pdf_export_entity_scoped(db_session: AsyncSession):
    role_admin = await get_or_create_role(db_session, RoleName.ADMIN)
    admin_user = User(email=f"admin_c_{uuid.uuid4().hex[:6]}@test.com", hashed_password="hash", full_name="Admin C", role_id=role_admin.id, is_active=True)
    db_session.add(admin_user)
    await db_session.flush()

    tier = CustomerTier(name=f"Tier-{uuid.uuid4().hex[:4]}")
    db_session.add(tier)
    await db_session.flush()

    cust_a = Customer(customer_code=f"CUST-A-{uuid.uuid4().hex[:4]}", name="Acme Corp Alpha", tier_id=tier.id, is_active=True)
    cust_b = Customer(customer_code=f"CUST-B-{uuid.uuid4().hex[:4]}", name="Zeta Inc Beta", tier_id=tier.id, is_active=True)
    db_session.add_all([cust_a, cust_b])
    await db_session.commit()

    service = ReportExportService(db_session)

    req_a = ReportExportRequest(report_type=ReportTypeEnum.CUSTOMER_360, format=ReportExportFormat.PDF, customer_id=cust_a.id)
    pdf_a, fn_a, _ = await service.export_report(req_a, admin_user)

    req_b = ReportExportRequest(report_type=ReportTypeEnum.CUSTOMER_360, format=ReportExportFormat.PDF, customer_id=cust_b.id)
    pdf_b, fn_b, _ = await service.export_report(req_b, admin_user)

    assert pdf_a.startswith(b"%PDF")
    assert pdf_b.startswith(b"%PDF")
    assert "Acme-Corp-Alpha" in fn_a
    assert "Zeta-Inc-Beta" in fn_b
    assert pdf_a != pdf_b


@pytest.mark.asyncio
async def test_customer_role_security_cross_access_denied(db_session: AsyncSession):
    role_admin = await get_or_create_role(db_session, RoleName.ADMIN)
    admin_user = User(email=f"admin_sec_{uuid.uuid4().hex[:6]}@test.com", hashed_password="hash", full_name="Admin Sec", role_id=role_admin.id, is_active=True)
    role_cust = await get_or_create_role(db_session, RoleName.CUSTOMER)
    db_session.add(admin_user)
    await db_session.flush()

    tier = CustomerTier(name=f"Tier-{uuid.uuid4().hex[:4]}")
    db_session.add(tier)
    await db_session.flush()

    cust_a = Customer(customer_code=f"CA-{uuid.uuid4().hex[:4]}", name="Customer A Corp", tier_id=tier.id, is_active=True)
    cust_b = Customer(customer_code=f"CB-{uuid.uuid4().hex[:4]}", name="Customer B Corp", tier_id=tier.id, is_active=True)
    db_session.add_all([cust_a, cust_b])
    await db_session.flush()

    user_a = User(email=f"user_a_{uuid.uuid4().hex[:6]}@test.com", hashed_password="hash", full_name="User A", role_id=role_cust.id, is_active=True)
    db_session.add(user_a)
    await db_session.flush()

    portal_access_a = CustomerPortalAccess(user_id=user_a.id, customer_id=cust_a.id, is_active=True)
    db_session.add(portal_access_a)

    quote_b = Quotation(quote_number=f"Q-B-{uuid.uuid4().hex[:4]}", customer_id=cust_b.id, sales_rep_id=admin_user.id, status="APPROVED", gross_subtotal=Decimal("500.00"), net_total=Decimal("500.00"))
    db_session.add(quote_b)
    await db_session.commit()

    service = ReportExportService(db_session)

    req_cross_quote = ReportExportRequest(report_type=ReportTypeEnum.QUOTATION, format=ReportExportFormat.PDF, quotation_id=quote_b.id)
    with pytest.raises(HTTPException) as exc_q:
        await service.export_report(req_cross_quote, user_a)
    assert exc_q.value.status_code == 403

    req_cross_cust = ReportExportRequest(report_type=ReportTypeEnum.CUSTOMER_360, format=ReportExportFormat.PDF, customer_id=cust_b.id)
    with pytest.raises(HTTPException) as exc_c:
        await service.export_report(req_cross_cust, user_a)
    assert exc_c.value.status_code == 403


@pytest.mark.asyncio
async def test_customer_role_security_own_access_allowed(db_session: AsyncSession):
    role_admin = await get_or_create_role(db_session, RoleName.ADMIN)
    admin_user = User(email=f"admin_sec2_{uuid.uuid4().hex[:6]}@test.com", hashed_password="hash", full_name="Admin Sec2", role_id=role_admin.id, is_active=True)
    role_cust = await get_or_create_role(db_session, RoleName.CUSTOMER)
    db_session.add(admin_user)
    await db_session.flush()

    tier = CustomerTier(name=f"Tier-{uuid.uuid4().hex[:4]}")
    db_session.add(tier)
    await db_session.flush()

    cust_a = Customer(customer_code=f"CA2-{uuid.uuid4().hex[:4]}", name="Customer A2 Corp", tier_id=tier.id, is_active=True)
    db_session.add(cust_a)
    await db_session.flush()

    user_a = User(email=f"user_a2_{uuid.uuid4().hex[:6]}@test.com", hashed_password="hash", full_name="User A2", role_id=role_cust.id, is_active=True)
    db_session.add(user_a)
    await db_session.flush()

    portal_access_a = CustomerPortalAccess(user_id=user_a.id, customer_id=cust_a.id, is_active=True)
    db_session.add(portal_access_a)

    quote_a = Quotation(quote_number=f"Q-A2-{uuid.uuid4().hex[:4]}", customer_id=cust_a.id, sales_rep_id=admin_user.id, status="APPROVED", gross_subtotal=Decimal("800.00"), net_total=Decimal("800.00"))
    db_session.add(quote_a)
    await db_session.commit()

    service = ReportExportService(db_session)

    req_own_quote = ReportExportRequest(report_type=ReportTypeEnum.QUOTATION, format=ReportExportFormat.PDF, quotation_id=quote_a.id)
    pdf_bytes, filename, mime_type = await service.export_report(req_own_quote, user_a)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert mime_type == "application/pdf"


@pytest.mark.asyncio
async def test_invoice_pdf_export_entity_scoped(db_session: AsyncSession):
    role_admin = await get_or_create_role(db_session, RoleName.ADMIN)
    admin_user = User(email=f"admin_inv_{uuid.uuid4().hex[:6]}@test.com", hashed_password="hash", full_name="Admin Inv", role_id=role_admin.id, is_active=True)
    db_session.add(admin_user)
    await db_session.flush()

    tier = CustomerTier(name=f"Tier-{uuid.uuid4().hex[:4]}")
    db_session.add(tier)
    await db_session.flush()

    cust = Customer(customer_code=f"C-INV-{uuid.uuid4().hex[:4]}", name="Invoice Cust Ltd", tier_id=tier.id, is_active=True)
    db_session.add(cust)
    await db_session.flush()

    quote = Quotation(quote_number=f"Q-INV-{uuid.uuid4().hex[:4]}", customer_id=cust.id, sales_rep_id=admin_user.id, status="APPROVED", gross_subtotal=Decimal("1200.00"), net_total=Decimal("1200.00"))
    db_session.add(quote)
    await db_session.flush()

    order = SalesOrder(order_number=f"SO-INV-{uuid.uuid4().hex[:4]}", quotation_id=quote.id, customer_id=cust.id, sales_rep_id=admin_user.id, status="CONFIRMED", gross_subtotal=Decimal("1200.00"), net_total=Decimal("1200.00"))
    db_session.add(order)
    await db_session.flush()

    inv = Invoice(invoice_number=f"INV-TEST-{uuid.uuid4().hex[:4]}", sales_order_id=order.id, customer_id=cust.id, invoice_type="ONE_TIME", status="ISSUED", subtotal=Decimal("1200.00"), total_amount=Decimal("1200.00"), balance_due=Decimal("1200.00"))
    db_session.add(inv)
    await db_session.commit()

    service = ReportExportService(db_session)
    req = ReportExportRequest(report_type=ReportTypeEnum.INVOICE, format=ReportExportFormat.PDF, invoice_id=inv.id)
    pdf_bytes, filename, mime_type = await service.export_report(req, admin_user)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert "DealFlow360_Invoice_" in filename
    assert mime_type == "application/pdf"

