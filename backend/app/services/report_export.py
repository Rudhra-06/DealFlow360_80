"""Report Export Service for Phase 6 Part 2."""

from datetime import datetime, timezone
from typing import Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.report_export_audit import ReportExportAudit, ExportStatus
from app.models.user import User
from app.repositories.report_export_audit import ReportExportAuditRepository
from app.schemas.reports import ReportExportRequest, ReportExportFormat, ReportTypeEnum
from app.services.analytics import AnalyticsService
from app.services.customer_360 import Customer360Service
from app.reports.pdf_renderer import PDFReportRenderer
from app.reports.xlsx_renderer import XLSXReportRenderer


class ReportExportService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.audit_repo = ReportExportAuditRepository(session)
        self.analytics_service = AnalyticsService(session)
        self.c360_service = Customer360Service(session)

    async def export_report(
        self, req: ReportExportRequest, current_user: User
    ) -> Tuple[bytes, str, str]:
        # Enforce RBAC
        user_role = current_user.role.name if current_user.role else ""
        if user_role == "CUSTOMER":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customers are not permitted to access report exports"
            )

        sales_rep_id = req.sales_rep_id
        if user_role == "SALES_REP":
            sales_rep_id = current_user.id


        # Retrieve dataset based on report_type
        title = req.report_type.value.replace("_", " ").title()
        data = {}

        try:
            if req.report_type == ReportTypeEnum.EXECUTIVE_SUMMARY:
                data = await self.analytics_service.get_overview(req.start_date, req.end_date, sales_rep_id)
            elif req.report_type == ReportTypeEnum.QUOTATION_FUNNEL:
                data = await self.analytics_service.get_quotation_funnel(req.start_date, req.end_date, sales_rep_id)
            elif req.report_type == ReportTypeEnum.SALES_PERFORMANCE:
                data = await self.analytics_service.get_sales_performance(req.start_date, req.end_date, sales_rep_id)
            elif req.report_type == ReportTypeEnum.CUSTOMER_360:
                if not req.customer_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="customer_id is required for CUSTOMER_360 report export"
                    )
                data = await self.c360_service.get_customer_360(req.customer_id, current_user)
            elif req.report_type == ReportTypeEnum.PRODUCT_PERFORMANCE:
                data = await self.analytics_service.get_products(req.start_date, req.end_date)
            elif req.report_type == ReportTypeEnum.APPROVAL_ANALYTICS:
                data = await self.analytics_service.get_approvals(req.start_date, req.end_date, sales_rep_id)
            elif req.report_type == ReportTypeEnum.NEGOTIATION_ANALYTICS:
                data = await self.analytics_service.get_negotiations(req.start_date, req.end_date, sales_rep_id)
            elif req.report_type == ReportTypeEnum.DEAL_HEALTH:
                data = await self.analytics_service.get_deal_health(sales_rep_id)
            elif req.report_type == ReportTypeEnum.FULFILLMENT:
                data = await self.analytics_service.get_fulfillment(req.start_date, req.end_date)
            elif req.report_type == ReportTypeEnum.BACKORDERS:
                data = await self.analytics_service.get_backorders(req.start_date, req.end_date)
            elif req.report_type == ReportTypeEnum.BILLING:
                data = await self.analytics_service.get_billing(req.start_date, req.end_date)
            elif req.report_type == ReportTypeEnum.RECEIVABLES:
                data = await self.analytics_service.get_receivables(req.end_date)
            elif req.report_type == ReportTypeEnum.SUBSCRIPTIONS:
                data = await self.analytics_service.get_subscriptions(req.start_date, req.end_date)
            else:
                data = await self.analytics_service.get_overview(req.start_date, req.end_date, sales_rep_id)
        except HTTPException:
            raise
        except Exception as e:
            # Audit failure
            date_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"dealflow360_{req.report_type.value.lower()}_{date_str}.{req.format.value.lower()}"
            audit = ReportExportAudit(
                user_id=current_user.id,
                report_type=req.report_type.value,
                format=req.format.value,
                filters_json=req.filters,
                start_date=req.start_date,
                end_date=req.end_date,
                status=ExportStatus.FAILED,
                filename=filename,
                error_message=str(e),
            )
            await self.audit_repo.add(audit)
            await self.session.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate report export: {str(e)}"
            )

        # Render file
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        ext = req.format.value.lower()
        filename = f"dealflow360_{req.report_type.value.lower()}_{date_str}.{ext}"

        if req.format == ReportExportFormat.PDF:
            file_bytes = PDFReportRenderer.render_report(req.report_type.value, data, title)
            mime_type = "application/pdf"
        else:
            file_bytes = XLSXReportRenderer.render_report(req.report_type.value, data, title)
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        # Record Audit
        audit = ReportExportAudit(
            user_id=current_user.id,
            report_type=req.report_type.value,
            format=req.format.value,
            filters_json=req.filters,
            start_date=req.start_date,
            end_date=req.end_date,
            row_count=len(data) if isinstance(data, list) else 1,
            status=ExportStatus.SUCCESS,
            filename=filename,
        )
        await self.audit_repo.add(audit)
        await self.session.commit()

        return file_bytes, filename, mime_type
