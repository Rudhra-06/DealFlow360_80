"""Report Export Service for Phase 6 Part 2."""

import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.report_export_audit import ReportExportAudit, ExportStatus
from app.models.user import User
from app.models.customer import Customer
from app.models.quotation import Quotation
from app.models.quotation_line import QuoteLine
from app.models.sales_order import SalesOrder
from app.models.invoice import Invoice
from app.models.invoice_line import InvoiceLine
from app.models.subscription import Subscription
from app.models.customer_portal_access import CustomerPortalAccess
from app.repositories.report_export_audit import ReportExportAuditRepository
from app.schemas.reports import ReportExportRequest, ReportExportFormat, ReportTypeEnum
from app.services.analytics import AnalyticsService
from app.services.customer_360 import Customer360Service
from app.reports.pdf_renderer import PDFReportRenderer
from app.reports.xlsx_renderer import XLSXReportRenderer


def sanitize_filename_part(text: str) -> str:
    if not text:
        return "doc"
    cleaned = re.sub(r"[^\w\-_]", "-", str(text).strip())
    cleaned = re.sub(r"-+", "-", cleaned)
    return cleaned.strip("-") or "doc"


class ReportExportService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.audit_repo = ReportExportAuditRepository(session)
        self.analytics_service = AnalyticsService(session)
        self.c360_service = Customer360Service(session)

    async def _verify_customer_portal_access(self, user_id: int, target_customer_id: int) -> None:
        p_stmt = select(CustomerPortalAccess).where(
            and_(
                CustomerPortalAccess.user_id == user_id,
                CustomerPortalAccess.is_active.is_(True),
            )
        )
        res = await self.session.execute(p_stmt)
        access = res.scalar_one_or_none()
        if not access or access.customer_id != target_customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this customer report",
            )

    async def _get_quotation_report_data(self, quotation_id: int, current_user: User) -> Dict[str, Any]:
        stmt = (
            select(Quotation)
            .where(Quotation.id == quotation_id)
            .options(
                selectinload(Quotation.customer).selectinload(Customer.tier),
                selectinload(Quotation.sales_rep),
                selectinload(Quotation.lines).selectinload(QuoteLine.product),
            )
        )
        res = await self.session.execute(stmt)
        quote = res.scalar_one_or_none()
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quotation with ID {quotation_id} not found",
            )

        user_role = current_user.role.name if (current_user and current_user.role) else ""
        if hasattr(user_role, "value"):
            user_role = user_role.value

        if user_role == "CUSTOMER":
            await self._verify_customer_portal_access(current_user.id, quote.customer_id)

        lines_data = []
        one_time_total = Decimal("0.00")
        recurring_total = Decimal("0.00")

        for line in quote.lines:
            prod_name = line.product.name if line.product else "Custom Line Item"
            prod_sku = line.product.sku if line.product else "N/A"
            is_recurring = getattr(line.product, "is_recurring", False) if line.product else False

            qty = line.quantity or 1
            list_price = Decimal(str(line.unit_list_price or Decimal("0.00")))
            disc_pct = Decimal(str(line.line_discount_pct or Decimal("0.00")))
            
            if getattr(line, "net_line_total", None) is not None:
                extended = Decimal(str(line.net_line_total)).quantize(Decimal("0.01"))
                net_unit = (extended / Decimal(str(qty))).quantize(Decimal("0.01"))
            else:
                net_unit = (list_price * (Decimal("1.00") - (disc_pct / Decimal("100.00")))).quantize(Decimal("0.01"))
                extended = (Decimal(str(qty)) * net_unit).quantize(Decimal("0.01"))

            if is_recurring:
                recurring_total += extended
            else:
                one_time_total += extended

            lines_data.append({
                "line_id": line.id,
                "product_name": prod_name,
                "sku": prod_sku,
                "quantity": qty,
                "unit_list_price": list_price,
                "discount_pct": disc_pct,
                "unit_net_price": net_unit,
                "extended_amount": extended,
                "is_recurring": is_recurring,
                "billing_type": "Recurring" if is_recurring else "One-Time",
            })

        cust = quote.customer
        rep = quote.sales_rep

        return {
            "quotation_id": quote.id,
            "quote_number": quote.quote_number,
            "version_number": getattr(quote, "version", getattr(quote, "version_number", 1)) or 1,
            "status": quote.status,
            "currency": quote.currency or "USD",
            "payment_terms_days": quote.payment_terms_days or 30,
            "created_at": quote.created_at,
            "valid_until": getattr(quote, "valid_until", None),
            "order_discount_pct": Decimal(str(quote.order_discount_pct or Decimal("0.00"))),
            "order_discount_amount": Decimal(str(quote.discount_amount or Decimal("0.00"))),
            "subtotal_amount": Decimal(str(quote.gross_subtotal or (one_time_total + recurring_total))),
            "net_total_amount": Decimal(str(quote.net_total or (one_time_total + recurring_total))),
            "one_time_subtotal": one_time_total,
            "recurring_subtotal": recurring_total,
            "invoice_number": f"INV-{quote.quote_number}",
            "invoice_type": "One-Time & Recurring",
            "issue_date": quote.created_at,
            "due_date": getattr(quote, "valid_until", None) or quote.created_at,
            "terms": f"Net {quote.payment_terms_days or 30}",
            "subtotal": Decimal(str(quote.gross_subtotal or (one_time_total + recurring_total))),
            "tax_amount": Decimal("0.00"),
            "total_amount": Decimal(str(quote.net_total or (one_time_total + recurring_total))),
            "paid_amount": Decimal("0.00"),
            "balance_due": Decimal(str(quote.net_total or (one_time_total + recurring_total))),
            "customer": {
                "id": cust.id if cust else None,
                "name": cust.name if cust else "Unknown Customer",
                "customer_code": cust.customer_code if cust else "-",
                "contact_name": getattr(cust, "contact_name", None) or getattr(cust, "email", "-"),
                "email": getattr(cust, "email", "-"),
                "phone": getattr(cust, "phone", "-"),
                "billing_address": getattr(cust, "billing_address", None) or getattr(cust, "address", "-"),
                "city": getattr(cust, "city", None) or "-",
                "state": getattr(cust, "state", None) or "-",
                "country": getattr(cust, "country", None) or "-",
                "postal_code": getattr(cust, "postal_code", None) or "-",
                "tier_name": cust.tier.name if (cust and cust.tier) else "Standard",
            },
            "sales_rep": {
                "id": rep.id if rep else None,
                "full_name": rep.full_name if rep else (rep.email if rep else "Sales Representative"),
                "email": rep.email if rep else "-",
            },
            "lines": lines_data,
        }

    async def _get_customer_360_report_data(self, customer_id: int, current_user: User) -> Dict[str, Any]:
        user_role = current_user.role.name if (current_user and current_user.role) else ""
        if hasattr(user_role, "value"):
            user_role = user_role.value

        if user_role == "CUSTOMER":
            await self._verify_customer_portal_access(current_user.id, customer_id)

        customer = await self.session.get(Customer, customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID {customer_id} not found"
            )

        if user_role == "SALES_REP":
            assigned_rep_id = getattr(customer, "assigned_sales_rep_id", None)
            if assigned_rep_id is not None and assigned_rep_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this customer profile"
                )

        data = await self.c360_service.repo.get_customer_360(customer_id)
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer 360 data not found for customer {customer_id}"
            )

        q_stmt = select(Quotation).where(Quotation.customer_id == customer_id).order_by(desc(Quotation.created_at)).limit(20)
        quotes = (await self.session.execute(q_stmt)).scalars().all()
        data["quotations_list"] = [
            {
                "quote_number": q.quote_number,
                "version_number": getattr(q, "version", getattr(q, "version_number", 1)) or 1,
                "created_at": q.created_at,
                "status": q.status,
                "net_total": q.net_total,
                "currency": q.currency or "USD",
            }
            for q in quotes
        ]

        o_stmt = select(SalesOrder).where(SalesOrder.customer_id == customer_id).order_by(desc(SalesOrder.created_at)).limit(20)
        orders = (await self.session.execute(o_stmt)).scalars().all()
        data["orders_list"] = [
            {
                "order_number": o.order_number,
                "quote_number": o.quotation.quote_number if hasattr(o, "quotation") and o.quotation else "-",
                "created_at": o.created_at,
                "status": o.status,
                "net_total": o.net_total,
                "currency": o.currency or "USD",
            }
            for o in orders
        ]

        inv_stmt = select(Invoice).where(Invoice.customer_id == customer_id).order_by(desc(Invoice.created_at)).limit(20)
        invoices = (await self.session.execute(inv_stmt)).scalars().all()
        data["invoices_list"] = [
            {
                "invoice_number": inv.invoice_number,
                "created_at": inv.created_at,
                "due_date": inv.due_date,
                "status": inv.status,
                "total_amount": inv.total_amount,
                "balance_due": inv.balance_due,
                "currency": inv.currency or "USD",
            }
            for inv in invoices
        ]

        sub_stmt = select(Subscription).where(Subscription.customer_id == customer_id).order_by(desc(Subscription.created_at)).limit(20)
        subs = (await self.session.execute(sub_stmt)).scalars().all()
        data["subscriptions_list"] = [
            {
                "subscription_number": s.subscription_number,
                "plan_name": f"Plan #{s.billing_plan_id}" if s.billing_plan_id else "Recurring Plan",
                "quantity": s.quantity or 1,
                "status": s.status,
                "monthly_recurring_revenue": s.monthly_recurring_revenue,
                "next_billing_date": s.next_billing_date,
                "currency": s.currency or "USD",
            }
            for s in subs
        ]

        return data

    async def _get_invoice_report_data(self, invoice_id: int, current_user: User) -> Dict[str, Any]:
        user_role = current_user.role.name if (current_user and current_user.role) else ""
        if hasattr(user_role, "value"):
            user_role = user_role.value

        stmt = select(Invoice).options(
            selectinload(Invoice.lines),
            selectinload(Invoice.customer),
            selectinload(Invoice.sales_order).selectinload(SalesOrder.quotation)
        ).where(Invoice.id == invoice_id)

        res = await self.session.execute(stmt)
        invoice = res.scalar_one_or_none()

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice with ID {invoice_id} not found"
            )

        if user_role == "CUSTOMER":
            await self._verify_customer_portal_access(current_user.id, invoice.customer_id)

        lines_data = []
        if invoice.lines:
            for line in invoice.lines:
                lines_data.append({
                    "description": line.description,
                    "quantity": Decimal(str(line.quantity or 1)),
                    "unit_price": Decimal(str(line.unit_price or 0)),
                    "amount": Decimal(str(line.amount or 0)),
                    "line_type": line.line_type or "ONE_TIME"
                })

        if not lines_data and invoice.sales_order and invoice.sales_order.quotation:
            q = invoice.sales_order.quotation
            q_stmt = select(QuoteLine).options(selectinload(QuoteLine.product)).where(QuoteLine.quotation_id == q.id)
            q_lines = (await self.session.execute(q_stmt)).scalars().all()
            for ql in q_lines:
                prod_name = ql.product.name if ql.product else "Product Item"
                lines_data.append({
                    "description": prod_name,
                    "quantity": Decimal(str(ql.quantity or 1)),
                    "unit_price": Decimal(str(ql.unit_net_price or ql.unit_list_price or 0)),
                    "amount": Decimal(str(ql.net_line_total or ql.gross_line_total or 0)),
                    "line_type": "Recurring" if ql.is_recurring else "ONE_TIME"
                })

        cust = invoice.customer
        so = invoice.sales_order
        q = so.quotation if so else None

        payment_terms = f"Net {q.payment_terms_days}" if (q and getattr(q, "payment_terms_days", None)) else "Net 30"

        return {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "invoice_type": invoice.invoice_type,
            "status": invoice.status,
            "currency": invoice.currency or "USD",
            "issue_date": invoice.created_at,
            "due_date": invoice.due_date,
            "terms": payment_terms,
            "sales_order_number": so.order_number if so else "-",
            "subtotal": Decimal(str(invoice.subtotal or 0)),
            "tax_amount": Decimal(str(invoice.tax_amount or 0)),
            "total_amount": Decimal(str(invoice.total_amount or 0)),
            "paid_amount": Decimal(str(invoice.paid_amount or 0)),
            "balance_due": Decimal(str(invoice.balance_due or 0)),
            "credited_amount": Decimal(str(invoice.credited_amount or 0)),
            "customer": {
                "id": cust.id if cust else None,
                "name": cust.name if cust else "Unknown Customer",
                "customer_code": cust.customer_code if cust else "-",
                "contact_name": getattr(cust, "contact_name", None) or getattr(cust, "email", "-"),
                "email": getattr(cust, "email", "-"),
                "phone": getattr(cust, "phone", "-"),
                "billing_address": getattr(cust, "billing_address", None) or getattr(cust, "address", "-"),
                "city": getattr(cust, "city", None) or "-",
                "state": getattr(cust, "state", None) or "-",
                "country": getattr(cust, "country", None) or "-",
                "postal_code": getattr(cust, "postal_code", None) or "-",
            },
            "lines": lines_data,
        }

    async def export_report(
        self, req: ReportExportRequest, current_user: User
    ) -> Tuple[bytes, str, str]:
        user_role = current_user.role.name if (current_user and current_user.role) else ""
        if hasattr(user_role, "value"):
            user_role = user_role.value

        if user_role == "CUSTOMER" and req.report_type not in (ReportTypeEnum.QUOTATION, ReportTypeEnum.CUSTOMER_360, ReportTypeEnum.INVOICE):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customers are not permitted to access internal operational reports"
            )

        sales_rep_id = req.sales_rep_id
        if user_role == "SALES_REP":
            sales_rep_id = current_user.id

        title = req.report_type.value.replace("_", " ").title()
        data = {}
        custom_filename = None

        try:
            if req.report_type == ReportTypeEnum.QUOTATION:
                if not req.quotation_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="quotation_id is required for QUOTATION report export"
                    )
                data = await self._get_quotation_report_data(req.quotation_id, current_user)
                quote_num = sanitize_filename_part(data.get("quote_number", "QT"))
                cust_name = sanitize_filename_part(data.get("customer", {}).get("name", "Customer"))
                custom_filename = f"DealFlow360_Quotation_{quote_num}_{cust_name}.{req.format.value.lower()}"

            elif req.report_type == ReportTypeEnum.INVOICE:
                if not req.invoice_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="invoice_id is required for INVOICE report export"
                    )
                data = await self._get_invoice_report_data(req.invoice_id, current_user)
                inv_num = sanitize_filename_part(data.get("invoice_number", "INV"))
                cust_name = sanitize_filename_part(data.get("customer", {}).get("name", "Customer"))
                custom_filename = f"DealFlow360_Invoice_{inv_num}_{cust_name}.{req.format.value.lower()}"

            elif req.report_type == ReportTypeEnum.CUSTOMER_360:
                if not req.customer_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="customer_id is required for CUSTOMER_360 report export"
                    )
                data = await self._get_customer_360_report_data(req.customer_id, current_user)
                cust_name = sanitize_filename_part(data.get("customer", {}).get("name", "Customer"))
                date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                custom_filename = f"DealFlow360_Customer_Report_{cust_name}_{date_str}.{req.format.value.lower()}"

            elif req.report_type == ReportTypeEnum.EXECUTIVE_SUMMARY:
                data = await self.analytics_service.get_overview(req.start_date, req.end_date, sales_rep_id)
            elif req.report_type == ReportTypeEnum.QUOTATION_FUNNEL:
                data = await self.analytics_service.get_quotation_funnel(req.start_date, req.end_date, sales_rep_id)
            elif req.report_type == ReportTypeEnum.SALES_PERFORMANCE:
                data = await self.analytics_service.get_sales_performance(req.start_date, req.end_date, sales_rep_id)
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
                if req.invoice_id:
                    data = await self._get_invoice_report_data(req.invoice_id, current_user)
                    req.report_type = ReportTypeEnum.INVOICE
                    inv_num = sanitize_filename_part(data.get("invoice_number", "INV"))
                    cust_name = sanitize_filename_part(data.get("customer", {}).get("name", "Customer"))
                    custom_filename = f"DealFlow360_Invoice_{inv_num}_{cust_name}.{req.format.value.lower()}"
                elif req.quotation_id:
                    data = await self._get_quotation_report_data(req.quotation_id, current_user)
                    req.report_type = ReportTypeEnum.INVOICE
                    inv_num = sanitize_filename_part(data.get("invoice_number", "INV"))
                    cust_name = sanitize_filename_part(data.get("customer", {}).get("name", "Customer"))
                    custom_filename = f"DealFlow360_Invoice_{inv_num}_{cust_name}.{req.format.value.lower()}"
                else:
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
            date_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = custom_filename or f"dealflow360_{req.report_type.value.lower()}_{date_str}.{req.format.value.lower()}"
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

        date_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        ext = req.format.value.lower()
        filename = custom_filename or f"dealflow360_{req.report_type.value.lower()}_{date_str}.{ext}"

        if req.format == ReportExportFormat.PDF:
            file_bytes = PDFReportRenderer.render_report(req.report_type.value, data, title)
            mime_type = "application/pdf"
        else:
            file_bytes = XLSXReportRenderer.render_report(req.report_type.value, data, title)
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

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
