"""Professional, entity-specific PDF Report Renderer using ReportLab."""

import io
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def escape_text(text: Any) -> str:
    if text is None:
        return "-"
    s = str(text).strip()
    if not s or s.lower() == "none":
        return "-"
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fmt_money(val: Any, currency: str = "USD") -> str:
    if val is None:
        return f"{currency} 0.00"
    try:
        d = Decimal(str(val))
        return f"{currency} {d:,.2f}"
    except Exception:
        return f"{currency} {val}"


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and draw total page counts."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        footer_text = "DealFlow360 B2B Commercial Systems — Official Report"
        page_text = f"Page {self._pageNumber} of {page_count}"

        self.drawString(36, 20, footer_text)
        self.drawRightString(576, 20, page_text)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.75)
        self.line(36, 32, 576, 32)
        self.restoreState()


class PDFReportRenderer:
    @staticmethod
    def render_report(report_type: str, data: Dict[str, Any], title: str = "") -> bytes:
        if report_type == "QUOTATION":
            return PDFReportRenderer.render_quotation_pdf(data)
        elif report_type == "INVOICE":
            return PDFReportRenderer.render_invoice_pdf(data)
        elif report_type == "CUSTOMER_360":
            return PDFReportRenderer.render_customer_360_pdf(data)
        else:
            return PDFReportRenderer.render_generic_report_pdf(report_type, data, title)

    # ----------------------------------------------------
    # 1. INDIVIDUAL QUOTATION PDF RENDERER
    # ----------------------------------------------------
    @staticmethod
    def render_quotation_pdf(data: Dict[str, Any]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=48,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#172A46"),
            spaceAfter=2,
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#64748B"),
        )
        doc_type_style = ParagraphStyle(
            "DocTypeHeader",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            alignment=2,
            textColor=colors.HexColor("#19B5A5"),
        )
        doc_sub_right = ParagraphStyle(
            "DocSubRight",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            alignment=2,
            textColor=colors.HexColor("#64748B"),
        )
        section_style = ParagraphStyle(
            "DocSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#172A46"),
            spaceBefore=8,
            spaceAfter=4,
        )
        label_bold = ParagraphStyle(
            "LabelBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#172A46"),
        )
        text_norm = ParagraphStyle(
            "TextNorm",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1E293B"),
        )
        text_right = ParagraphStyle(
            "TextRight",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            alignment=2,
            textColor=colors.HexColor("#1E293B"),
        )
        text_right_bold = ParagraphStyle(
            "TextRightBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            alignment=2,
            textColor=colors.HexColor("#172A46"),
        )
        tbl_header = ParagraphStyle(
            "TblHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=colors.whitesmoke,
        )
        tbl_header_right = ParagraphStyle(
            "TblHeaderRight",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            alignment=2,
            textColor=colors.whitesmoke,
        )

        elements = []

        currency = data.get("currency", "USD")
        quote_num = data.get("quote_number", "QT-DRAFT")
        version_num = data.get("version_number", 1)
        status_str = data.get("status", "DRAFT").replace("_", " ").title()

        created_at = data.get("created_at")
        if isinstance(created_at, datetime):
            date_str = created_at.strftime("%Y-%m-%d")
        else:
            date_str = str(created_at)[:10] if created_at else datetime.now(timezone.utc).strftime("%Y-%m-%d")

        valid_until = data.get("valid_until")
        if isinstance(valid_until, datetime):
            valid_str = valid_until.strftime("%Y-%m-%d")
        elif valid_until:
            valid_str = str(valid_until)[:10]
        else:
            valid_str = "-"

        cust = data.get("customer", {})
        sales_rep = data.get("sales_rep", {})

        # Header Table: Company Branding Left vs Document Reference Right
        hdr_left = [
            Paragraph("DealFlow360", title_style),
            Paragraph("Enterprise Commercial CPQ & Billing Systems", subtitle_style),
        ]
        hdr_right = [
            Paragraph("COMMERCIAL QUOTATION", doc_type_style),
            Paragraph(f"Ref: <b>{quote_num}</b> (v{version_num})", doc_sub_right),
            Paragraph(f"Date: {date_str} | Status: <b>{status_str}</b>", doc_sub_right),
        ]
        hdr_table = Table([[hdr_left, hdr_right]], colWidths=[300, 240])
        hdr_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(hdr_table)
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#172A46"), spaceAfter=12))

        # 2-Column Info Table: Bill To vs Commercial Details
        cust_lines = [
            Paragraph("<b>CUSTOMER / BILL TO</b>", section_style),
            Paragraph(f"<b>{escape_text(cust.get('name'))}</b>", label_bold),
            Paragraph(f"Customer Code: {escape_text(cust.get('customer_code'))}", text_norm),
            Paragraph(f"Contact: {escape_text(cust.get('contact_name'))}", text_norm),
            Paragraph(f"Billing Address: {escape_text(cust.get('billing_address'))}", text_norm),
            Paragraph(f"City/State/Country: {escape_text(cust.get('city'))}, {escape_text(cust.get('country'))}", text_norm),
            Paragraph(f"Email: {escape_text(cust.get('email'))} | Phone: {escape_text(cust.get('phone'))}", text_norm),
        ]

        details_lines = [
            Paragraph("<b>QUOTATION DETAILS</b>", section_style),
            Paragraph(f"Quotation Number: <b>{quote_num}</b>", text_norm),
            Paragraph(f"Revision Snapshot: <b>Version {version_num}</b>", text_norm),
            Paragraph(f"Issue Date: <b>{date_str}</b>", text_norm),
            Paragraph(f"Valid Until: <b>{valid_str}</b>", text_norm),
            Paragraph(f"Payment Terms: <b>Net {data.get('payment_terms_days', 30)} Days</b>", text_norm),
            Paragraph(f"Currency: <b>{currency}</b>", text_norm),
            Paragraph(f"Sales Representative: <b>{escape_text(sales_rep.get('full_name'))}</b>", text_norm),
        ]

        info_table = Table([[cust_lines, details_lines]], colWidths=[270, 270])
        info_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#F8FAFC")),
            ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#F8FAFC")),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("BOX", (0, 0), (0, 0), 0.5, colors.HexColor("#CBD5E1")),
            ("BOX", (1, 0), (1, 0), 0.5, colors.HexColor("#CBD5E1")),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 14))

        # Line Items Table
        elements.append(Paragraph("<b>COMMERCIAL LINE ITEMS</b>", section_style))
        lines = data.get("lines", [])

        col_w = [170, 65, 40, 75, 55, 65, 70]
        tbl_data = [
            [
                Paragraph("Description", tbl_header),
                Paragraph("SKU", tbl_header),
                Paragraph("Qty", tbl_header_right),
                Paragraph("List Price", tbl_header_right),
                Paragraph("Disc %", tbl_header_right),
                Paragraph("Net Price", tbl_header_right),
                Paragraph("Amount", tbl_header_right),
            ]
        ]

        for line in lines:
            p_desc = f"<b>{escape_text(line.get('product_name'))}</b>"
            if line.get("billing_type"):
                p_desc += f"<br/><font color='#64748B' size=7>[{escape_text(line.get('billing_type'))}]</font>"

            tbl_data.append([
                Paragraph(p_desc, text_norm),
                Paragraph(escape_text(line.get("sku")), text_norm),
                Paragraph(str(line.get("quantity", 1)), text_right),
                Paragraph(fmt_money(line.get("unit_list_price"), currency), text_right),
                Paragraph(f"{Decimal(str(line.get('discount_pct', 0))):.1f}%", text_right),
                Paragraph(fmt_money(line.get("unit_net_price"), currency), text_right),
                Paragraph(fmt_money(line.get("extended_amount"), currency), text_right),
            ])

        if not lines:
            tbl_data.append([
                Paragraph("<i>No product line items available for this quotation.</i>", text_norm),
                Paragraph("-", text_norm), Paragraph("-", text_right), Paragraph("-", text_right),
                Paragraph("-", text_right), Paragraph("-", text_right), Paragraph("-", text_right)
            ])

        line_table = Table(tbl_data, colWidths=col_w, repeatRows=1)
        line_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172A46")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ]))
        elements.append(line_table)
        elements.append(Spacer(1, 10))

        # Financial Totals Box
        gross_sub = data.get("subtotal_amount", Decimal("0.00"))
        disc_amt = data.get("order_discount_amount", Decimal("0.00"))
        net_tot = data.get("net_total_amount", Decimal("0.00"))

        tot_data = [
            [Paragraph("Subtotal Gross Amount:", label_bold), Paragraph(fmt_money(gross_sub, currency), text_right)],
        ]
        if Decimal(str(disc_amt)) > 0:
            tot_data.append([Paragraph("Total Order Discount:", label_bold), Paragraph(f"- {fmt_money(disc_amt, currency)}", text_right)])
        tot_data.append([Paragraph("<b>TOTAL NET AMOUNT:</b>", section_style), Paragraph(f"<b>{fmt_money(net_tot, currency)}</b>", text_right_bold)])

        tot_table = Table(tot_data, colWidths=[150, 120])
        tot_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#172A46")),
        ]))

        outer_tot = Table([["", tot_table]], colWidths=[270, 270])
        outer_tot.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        elements.append(outer_tot)
        elements.append(Spacer(1, 14))

        # Terms & Conditions Block
        terms_text = [
            Paragraph("<b>COMMERCIAL TERMS & INSTRUCTIONS</b>", section_style),
            Paragraph(f"1. Payment is due within <b>{data.get('payment_terms_days', 30)} days</b> of invoice issuance.", text_norm),
            Paragraph("2. All prices are quoted exclusive of applicable statutory sales tax unless specified.", text_norm),
            Paragraph("3. Delivery and fulfillment schedules align with DealFlow360 standard warehouse logistics terms.", text_norm),
            Paragraph("4. This quotation is generated automatically by DealFlow360 and subject to contractual terms.", text_norm),
        ]
        terms_box = Table([[terms_text]], colWidths=[540])
        terms_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#F8FAFC")),
            ("PADDING", (0, 0), (0, 0), 8),
            ("BOX", (0, 0), (0, 0), 0.5, colors.HexColor("#CBD5E1")),
        ]))
        elements.append(KeepTogether(terms_box))

        doc.build(elements, canvasmaker=NumberedCanvas)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    # ----------------------------------------------------
    # 2. INDIVIDUAL CUSTOMER ACTIVITY PDF RENDERER
    # ----------------------------------------------------
    @staticmethod
    def render_customer_360_pdf(data: Dict[str, Any], show_internal_risk: bool = True) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=48,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#172A46"),
            spaceAfter=2,
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#64748B"),
        )
        doc_type_style = ParagraphStyle(
            "DocTypeHeader",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            alignment=2,
            textColor=colors.HexColor("#19B5A5"),
        )
        doc_sub_right = ParagraphStyle(
            "DocSubRight",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            alignment=2,
            textColor=colors.HexColor("#64748B"),
        )
        section_style = ParagraphStyle(
            "DocSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#172A46"),
            spaceBefore=10,
            spaceAfter=4,
        )
        label_bold = ParagraphStyle(
            "LabelBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#172A46"),
        )
        text_norm = ParagraphStyle(
            "TextNorm",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#1E293B"),
        )
        text_right = ParagraphStyle(
            "TextRight",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            alignment=2,
            textColor=colors.HexColor("#1E293B"),
        )
        tbl_header = ParagraphStyle(
            "TblHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.whitesmoke,
        )
        tbl_header_right = ParagraphStyle(
            "TblHeaderRight",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            alignment=2,
            textColor=colors.whitesmoke,
        )

        elements = []

        profile = data.get("customer", {})
        cust_name = profile.get("name", "Customer Account")
        cust_code = profile.get("customer_code", "-")
        tier_name = profile.get("customer_tier", "Standard")
        sales_rep = profile.get("assigned_sales_rep", "Unassigned")

        gen_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        # Header Block
        hdr_left = [
            Paragraph("DealFlow360", title_style),
            Paragraph("Customer Portfolio & Activity Analysis", subtitle_style),
        ]
        hdr_right = [
            Paragraph("CUSTOMER ACTIVITY REPORT", doc_type_style),
            Paragraph(f"Account: <b>{escape_text(cust_name)}</b> ({cust_code})", doc_sub_right),
            Paragraph(f"Generated: {gen_time}", doc_sub_right),
        ]
        hdr_table = Table([[hdr_left, hdr_right]], colWidths=[300, 240])
        hdr_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        elements.append(hdr_table)
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#172A46"), spaceAfter=10))

        # Account Details Box
        details_col1 = [
            Paragraph(f"Customer Name: <b>{escape_text(cust_name)}</b>", text_norm),
            Paragraph(f"Customer Code: <b>{escape_text(cust_code)}</b>", text_norm),
            Paragraph(f"Customer Tier: <b>{escape_text(tier_name)}</b>", text_norm),
        ]
        details_col2 = [
            Paragraph(f"Assigned Sales Rep: <b>{escape_text(sales_rep)}</b>", text_norm),
            Paragraph(f"Account Status: <b>{'Active' if profile.get('is_active', True) else 'Inactive'}</b>", text_norm),
            Paragraph(f"Report Scope: <b>Scoped strictly to customer_id {profile.get('customer_id', '-')}</b>", text_norm),
        ]
        acc_box = Table([[details_col1, details_col2]], colWidths=[270, 270])
        acc_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ]))
        elements.append(acc_box)
        elements.append(Spacer(1, 10))

        # Account Summary Metrics
        comm = data.get("commercial", {})
        orders_summary = data.get("orders_data", {})
        billing_summary = data.get("billing", {})
        subs_summary = data.get("subscriptions", {})

        elements.append(Paragraph("<b>ACCOUNT ACTIVITY SUMMARY</b>", section_style))

        inv_by_curr = billing_summary.get("invoiced_value_by_currency", {})
        out_by_curr = billing_summary.get("outstanding_balance_by_currency", {})
        pay_by_curr = billing_summary.get("payments_received_by_currency", {})

        inv_str = ", ".join([f"{curr}: {fmt_money(val, curr)}" for curr, val in inv_by_curr.items()]) if inv_by_curr else "USD 0.00"
        out_str = ", ".join([f"{curr}: {fmt_money(val, curr)}" for curr, val in out_by_curr.items()]) if out_by_curr else "USD 0.00"
        pay_str = ", ".join([f"{curr}: {fmt_money(val, curr)}" for curr, val in pay_by_curr.items()]) if pay_by_curr else "USD 0.00"

        sum_tbl_data = [
            [Paragraph("Total Quotations:", label_bold), Paragraph(str(comm.get("total_quotations", 0)), text_norm),
             Paragraph("Total Sales Orders:", label_bold), Paragraph(str(orders_summary.get("total_orders", 0)), text_norm)],
            [Paragraph("Confirmed Deals:", label_bold), Paragraph(str(comm.get("confirmed_quotations", 0)), text_norm),
             Paragraph("Active Subscriptions:", label_bold), Paragraph(str(subs_summary.get("active_subscriptions", 0)), text_norm)],
            [Paragraph("Total Invoiced Value:", label_bold), Paragraph(inv_str, text_norm),
             Paragraph("Payments Received:", label_bold), Paragraph(pay_str, text_norm)],
            [Paragraph("Outstanding Balance:", label_bold), Paragraph(out_str, text_norm),
             Paragraph("Overdue Invoices:", label_bold), Paragraph(str(billing_summary.get("overdue_invoices", 0)), text_norm)],
        ]
        sum_table = Table(sum_tbl_data, colWidths=[130, 140, 130, 140])
        sum_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F1F5F9")),
            ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#F1F5F9")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(sum_table)
        elements.append(Spacer(1, 10))

        # Section 1: Customer Quotations Table
        elements.append(Paragraph("<b>RECENT ACCOUNT QUOTATIONS</b>", section_style))
        quotes_list = data.get("quotations_list", [])
        q_cols = [110, 65, 85, 110, 100, 70]
        q_tbl_data = [
            [
                Paragraph("Quote Number", tbl_header),
                Paragraph("Version", tbl_header),
                Paragraph("Date", tbl_header),
                Paragraph("Status", tbl_header),
                Paragraph("Total Amount", tbl_header_right),
                Paragraph("Currency", tbl_header_right),
            ]
        ]
        for q in quotes_list:
            d_s = str(q.get("created_at"))[:10] if q.get("created_at") else "-"
            st_s = str(q.get("status", "")).replace("_", " ").title()
            q_tbl_data.append([
                Paragraph(f"<b>{escape_text(q.get('quote_number'))}</b>", text_norm),
                Paragraph(f"v{q.get('version_number', 1)}", text_norm),
                Paragraph(d_s, text_norm),
                Paragraph(st_s, text_norm),
                Paragraph(fmt_money(q.get("net_total"), q.get("currency", "USD")), text_right),
                Paragraph(escape_text(q.get("currency")), text_right),
            ])
        if not quotes_list:
            q_tbl_data.append([Paragraph("<i>No quotations recorded for this customer.</i>", text_norm), Paragraph("-", text_norm), Paragraph("-", text_norm), Paragraph("-", text_norm), Paragraph("-", text_right), Paragraph("-", text_right)])

        q_table = Table(q_tbl_data, colWidths=q_cols, repeatRows=1)
        q_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172A46")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ]))
        elements.append(q_table)
        elements.append(Spacer(1, 10))

        # Section 2: Customer Orders Table
        elements.append(Paragraph("<b>SALES ORDERS & FULFILLMENT</b>", section_style))
        orders_list = data.get("orders_list", [])
        o_cols = [120, 110, 85, 105, 120]
        o_tbl_data = [
            [
                Paragraph("Order Number", tbl_header),
                Paragraph("Source Quote", tbl_header),
                Paragraph("Order Date", tbl_header),
                Paragraph("Fulfillment Status", tbl_header),
                Paragraph("Order Total", tbl_header_right),
            ]
        ]
        for o in orders_list:
            d_s = str(o.get("created_at"))[:10] if o.get("created_at") else "-"
            st_s = str(o.get("status", "")).replace("_", " ").title()
            o_tbl_data.append([
                Paragraph(f"<b>{escape_text(o.get('order_number'))}</b>", text_norm),
                Paragraph(escape_text(o.get("quote_number")), text_norm),
                Paragraph(d_s, text_norm),
                Paragraph(st_s, text_norm),
                Paragraph(fmt_money(o.get("net_total"), o.get("currency", "USD")), text_right),
            ])
        if not orders_list:
            o_tbl_data.append([Paragraph("<i>No sales orders recorded for this customer.</i>", text_norm), Paragraph("-", text_norm), Paragraph("-", text_norm), Paragraph("-", text_norm), Paragraph("-", text_right)])

        o_table = Table(o_tbl_data, colWidths=o_cols, repeatRows=1)
        o_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172A46")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ]))
        elements.append(o_table)
        elements.append(Spacer(1, 10))

        # Section 3: Invoices & Payment Activity Table
        elements.append(Paragraph("<b>INVOICES & REVENUE SETTLEMENT</b>", section_style))
        invoices_list = data.get("invoices_list", [])
        i_cols = [110, 75, 75, 80, 100, 100]
        i_tbl_data = [
            [
                Paragraph("Invoice Number", tbl_header),
                Paragraph("Issue Date", tbl_header),
                Paragraph("Due Date", tbl_header),
                Paragraph("Status", tbl_header),
                Paragraph("Total Amount", tbl_header_right),
                Paragraph("Balance Due", tbl_header_right),
            ]
        ]
        for inv in invoices_list:
            c_s = str(inv.get("created_at"))[:10] if inv.get("created_at") else "-"
            d_s = str(inv.get("due_date"))[:10] if inv.get("due_date") else "-"
            st_s = str(inv.get("status", "")).replace("_", " ").title()
            i_tbl_data.append([
                Paragraph(f"<b>{escape_text(inv.get('invoice_number'))}</b>", text_norm),
                Paragraph(c_s, text_norm),
                Paragraph(d_s, text_norm),
                Paragraph(st_s, text_norm),
                Paragraph(fmt_money(inv.get("total_amount"), inv.get("currency", "USD")), text_right),
                Paragraph(fmt_money(inv.get("balance_due"), inv.get("currency", "USD")), text_right),
            ])
        if not invoices_list:
            i_tbl_data.append([Paragraph("<i>No invoice records available for this customer.</i>", text_norm), Paragraph("-", text_norm), Paragraph("-", text_norm), Paragraph("-", text_norm), Paragraph("-", text_right), Paragraph("-", text_right)])

        i_table = Table(i_tbl_data, colWidths=i_cols, repeatRows=1)
        i_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172A46")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ]))
        elements.append(i_table)
        elements.append(Spacer(1, 10))

        # Section 4: Subscriptions Table
        elements.append(Paragraph("<b>RECURRING REVENUE & SUBSCRIPTIONS</b>", section_style))
        subs_list = data.get("subscriptions_list", [])
        s_cols = [120, 110, 60, 75, 85, 90]
        s_tbl_data = [
            [
                Paragraph("Subscription No", tbl_header),
                Paragraph("Plan Name", tbl_header),
                Paragraph("Qty", tbl_header_right),
                Paragraph("Status", tbl_header),
                Paragraph("MRR", tbl_header_right),
                Paragraph("Next Billing", tbl_header_right),
            ]
        ]
        for sub in subs_list:
            nb_s = str(sub.get("next_billing_date"))[:10] if sub.get("next_billing_date") else "-"
            st_s = str(sub.get("status", "")).replace("_", " ").title()
            s_tbl_data.append([
                Paragraph(f"<b>{escape_text(sub.get('subscription_number'))}</b>", text_norm),
                Paragraph(escape_text(sub.get("plan_name")), text_norm),
                Paragraph(str(sub.get("quantity", 1)), text_right),
                Paragraph(st_s, text_norm),
                Paragraph(fmt_money(sub.get("monthly_recurring_revenue"), sub.get("currency", "USD")), text_right),
                Paragraph(nb_s, text_right),
            ])
        if not subs_list:
            s_tbl_data.append([Paragraph("<i>No active subscriptions recorded.</i>", text_norm), Paragraph("-", text_norm), Paragraph("-", text_right), Paragraph("-", text_norm), Paragraph("-", text_right), Paragraph("-", text_right)])

        s_table = Table(s_tbl_data, colWidths=s_cols, repeatRows=1)
        s_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172A46")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ]))
        elements.append(s_table)

        doc.build(elements, canvasmaker=NumberedCanvas)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    # ----------------------------------------------------
    # 3. INDIVIDUAL INVOICE PDF RENDERER (Image 2 Template)
    # ----------------------------------------------------
    @staticmethod
    def render_invoice_pdf(data: Dict[str, Any]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=48,
        )

        styles = getSampleStyleSheet()

        company_style = ParagraphStyle(
            "CompanyInfo",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
        )
        logo_text_style = ParagraphStyle(
            "LogoText",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            alignment=2,
            textColor=colors.HexColor("#172A46"),
        )
        invoice_title_style = ParagraphStyle(
            "InvoiceTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#172A46"),
            spaceBefore=12,
            spaceAfter=8,
        )
        block_label_style = ParagraphStyle(
            "BlockLabel",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#172A46"),
            spaceAfter=4,
        )
        block_body_style = ParagraphStyle(
            "BlockBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
        )
        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#172A46"),
        )
        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1E293B"),
        )
        thanks_style = ParagraphStyle(
            "ThanksStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#475569"),
        )

        story = []

        # 1. Company Header (Left) & Logo / Brand (Right)
        comp_text = "<b>DealFlow360 B2B Systems Inc.</b><br/>100 Enterprise Way, Suite 400<br/>San Francisco, CA 94105, USA<br/>Phone: +1 (800) 555-0199<br/>Email: billing@dealflow360.com"
        comp_p = Paragraph(comp_text, company_style)
        logo_p = Paragraph("<b>DealFlow360</b>", logo_text_style)

        header_table = Table([[comp_p, logo_p]], colWidths=[340, 200])
        header_table.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ])
        )
        story.append(header_table)

        # 2. Horizontal Divider Line
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#475569"), spaceBefore=4, spaceAfter=12))

        # 3. Bill To & Invoice Details Grid
        cust = data.get("customer", {})
        cust_name = escape_text(cust.get("name", "Customer Name"))
        contact_name = escape_text(cust.get("contact_name", cust.get("email", "-")))
        address = escape_text(cust.get("billing_address", cust.get("address", "-")))
        city = escape_text(cust.get("city", "-"))
        state = escape_text(cust.get("state", "-"))
        country = escape_text(cust.get("country", "-"))
        postal = escape_text(cust.get("postal_code", "-"))

        bill_to_text = f"<b>BILL TO</b><br/>{contact_name}<br/>{cust_name}<br/>{address}<br/>{city}, {state}, {country}<br/>{postal}"
        bill_to_p = Paragraph(bill_to_text, block_body_style)

        currency = data.get("currency", "USD")
        inv_num = escape_text(data.get("invoice_number", data.get("quote_number", "INV-1234")))
        inv_type = escape_text(data.get("invoice_type", "ONE_TIME")).replace("_", " ").title()
        status_text = escape_text(data.get("status", "ISSUED")).replace("_", " ").title()

        issue_date_raw = data.get("issue_date") or data.get("created_at")
        issue_date_str = issue_date_raw.strftime("%m/%d/%Y") if isinstance(issue_date_raw, datetime) else str(issue_date_raw or "-")[:10]

        due_date_raw = data.get("due_date") or data.get("valid_until")
        due_date_str = due_date_raw.strftime("%m/%d/%Y") if isinstance(due_date_raw, datetime) else str(due_date_raw or "-")[:10]

        terms_str = escape_text(data.get("terms", "Net 30"))

        subtotal = data.get("subtotal", data.get("subtotal_amount", Decimal("0.00")))
        tax_amount = data.get("tax_amount", Decimal("0.00"))
        total_amount = data.get("total_amount", data.get("net_total_amount", Decimal("0.00")))
        paid_amount = data.get("paid_amount", Decimal("0.00"))
        balance_due = data.get("balance_due", Decimal(str(total_amount)) - Decimal(str(paid_amount)))

        total_amt_str = fmt_money(total_amount, currency)
        paid_amt_str = fmt_money(paid_amount, currency)
        balance_due_str = fmt_money(balance_due, currency)

        inv_details_text = (
            f"<b>INVOICE DETAILS</b><br/>"
            f"<b>Invoice Number:</b> {inv_num}<br/>"
            f"<b>Type:</b> {inv_type}<br/>"
            f"<b>Issue Date:</b> {issue_date_str}<br/>"
            f"<b>Due Date:</b> {due_date_str}<br/>"
            f"<b>Terms:</b> {terms_str}<br/>"
            f"<b>Status:</b> {status_text}<br/>"
            f"<b>Total Amount:</b> {total_amt_str}<br/>"
            f"<b>Paid:</b> {paid_amt_str}<br/>"
            f"<b>Balance Due:</b> {balance_due_str}"
        )
        inv_details_p = Paragraph(inv_details_text, block_body_style)

        details_table = Table([[bill_to_p, inv_details_p]], colWidths=[270, 270])
        details_table.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ])
        )
        story.append(details_table)

        # 4. Document Title: INVOICE
        story.append(Paragraph("INVOICE", invoice_title_style))
        story.append(Spacer(1, 4))

        # 5. Line Items Table
        # Columns: DESCRIPTION | QUANTITY | UNIT PRICE | AMOUNT
        table_data = [
            [
                Paragraph("DESCRIPTION", table_header_style),
                Paragraph("QUANTITY", table_header_style),
                Paragraph("UNIT PRICE", table_header_style),
                Paragraph("AMOUNT", table_header_style),
            ]
        ]

        currency = data.get("currency", "USD")
        lines = data.get("lines", [])

        if not lines:
            table_data.append([
                Paragraph("No invoice line items available.", table_cell_style),
                Paragraph("1", table_cell_style),
                Paragraph(fmt_money(0, currency), table_cell_style),
                Paragraph(fmt_money(0, currency), table_cell_style),
            ])
        else:
            for item in lines:
                desc = escape_text(item.get("description", "Product Item"))
                qty = item.get("quantity", 1)
                unit_price = item.get("unit_price", 0)
                amount = item.get("amount", 0)

                qty_str = f"{Decimal(str(qty)):g}"
                unit_price_str = fmt_money(unit_price, currency)
                amount_str = fmt_money(amount, currency)

                table_data.append([
                    Paragraph(desc, table_cell_style),
                    Paragraph(qty_str, table_cell_style),
                    Paragraph(unit_price_str, table_cell_style),
                    Paragraph(amount_str, table_cell_style),
                ])

        items_table = Table(table_data, colWidths=[260, 70, 105, 105], repeatRows=1)
        items_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ])
        )
        story.append(items_table)
        story.append(Spacer(1, 16))

        # 6. Bottom Totals Section (Right) & Thank You message (Left)
        subtotal = data.get("subtotal", Decimal("0.00"))
        tax_amount = data.get("tax_amount", Decimal("0.00"))
        total_amount = data.get("total_amount", Decimal("0.00"))
        paid_amount = data.get("paid_amount", Decimal("0.00"))
        balance_due = data.get("balance_due", Decimal("0.00"))

        thanks_p = Paragraph("Thank you for your business!", thanks_style)

        totals_rows = [
            [Paragraph("<b>SUBTOTAL</b>", block_body_style), Paragraph(fmt_money(subtotal, currency), block_body_style)],
            [Paragraph("<b>TAX (0%)</b>", block_body_style), Paragraph(fmt_money(tax_amount, currency), block_body_style)],
            [Paragraph("<b>TOTAL</b>", block_label_style), Paragraph(f"<b>{fmt_money(total_amount, currency)}</b>", block_label_style)],
            [Paragraph("<b>PAID TO DATE</b>", block_body_style), Paragraph(fmt_money(paid_amount, currency), block_body_style)],
            [Paragraph("<b>BALANCE DUE</b>", block_label_style), Paragraph(f"<b>{fmt_money(balance_due, currency)}</b>", block_label_style)],
        ]
        totals_table = Table(totals_rows, colWidths=[120, 110])
        totals_table.setStyle(
            TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 1), (1, 1), 0.5, colors.HexColor("#CBD5E1")),
                ("LINEBELOW", (0, 3), (1, 3), 0.5, colors.HexColor("#CBD5E1")),
            ])
        )

        bottom_table = Table([[thanks_p, totals_table]], colWidths=[310, 230])
        bottom_table.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ])
        )

        story.append(KeepTogether([bottom_table]))

        doc.build(story, canvasmaker=NumberedCanvas)
        buffer.seek(0)
        return buffer.getvalue()

    # ----------------------------------------------------
    # 4. GENERIC / SYSTEM SUMMARY PDF RENDERER
    # ----------------------------------------------------
    @staticmethod
    def render_generic_report_pdf(report_type: str, data: Dict[str, Any], title: str) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=48,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#172A46"),
            spaceAfter=4,
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=12,
        )
        section_style = ParagraphStyle(
            "DocSection",
            parent=styles["Heading2"],
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#19B5A5"),
            spaceBefore=10,
            spaceAfter=6,
        )
        body_style = styles["Normal"]

        elements = []

        elements.append(Paragraph(f"DealFlow360 — {escape_text(title or report_type)}", title_style))
        gen_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        elements.append(Paragraph(f"Generated At: {gen_time} | Global System Analytics Report", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=10))

        kpi_data = [["Metric Name", "Value"]]
        for k, v in data.items():
            if isinstance(v, (int, float, str, Decimal)) and k not in ["start_date", "end_date", "granularity"]:
                k_label = k.replace("_", " ").title()
                kpi_data.append([Paragraph(escape_text(k_label), body_style), Paragraph(escape_text(str(v)), body_style)])
            elif isinstance(v, dict) and all(isinstance(val, (int, float, str, Decimal)) for val in v.values()):
                k_label = k.replace("_", " ").title()
                val_str = ", ".join(f"{curr}: {val}" for curr, val in v.items())
                kpi_data.append([Paragraph(escape_text(k_label), body_style), Paragraph(escape_text(val_str), body_style)])

        if len(kpi_data) > 1:
            t = Table(kpi_data, colWidths=[240, 300])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172A46")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ]))
            elements.append(Paragraph("Executive System Metrics", section_style))
            elements.append(t)
            elements.append(Spacer(1, 15))

        doc.build(elements, canvasmaker=NumberedCanvas)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
