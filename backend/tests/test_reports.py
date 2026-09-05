"""Report Export Tests for Phase 6 Part 2."""

import pytest
import io
import openpyxl
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import RoleName
from app.models.user import User
from app.models.customer import Customer
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
    # Test formula protection
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

    # Open with openpyxl to verify valid workbook
    wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes))
    assert "Summary" in wb.sheetnames


@pytest.mark.asyncio
async def test_report_export_service_and_audit(db_session: AsyncSession):
    role_admin = await get_or_create_role(db_session, RoleName.ADMIN)
    user = User(email="report_admin@test.com", password_hash="hash", full_name="Report Admin", is_active=True)
    user.roles.append(role_admin)
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
async def test_customer_role_export_403(db_session: AsyncSession):
    role_cust = await get_or_create_role(db_session, RoleName.CUSTOMER)
    cust_user = User(email="cust_user@test.com", password_hash="hash", full_name="Cust User", is_active=True)
    cust_user.roles.append(role_cust)
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
