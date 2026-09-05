"""PDF Report Renderer using ReportLab."""

import io
from datetime import datetime, timezone
from typing import Any, Dict, List
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak


def escape_text(text: Any) -> str:
    if text is None:
        return ""
    s = str(text)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class PDFReportRenderer:
    @staticmethod
    def render_report(report_type: str, data: Dict[str, Any], title: str) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter) if "PERFORMANCE" in report_type or "360" in report_type else letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=6,
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=12,
        )
        section_style = ParagraphStyle(
            "DocSection",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#0f766e"),
            spaceBefore=10,
            spaceAfter=6,
        )
        body_style = styles["Normal"]

        elements = []

        # Title Block
        elements.append(Paragraph(f"DealFlow360 — {escape_text(title)}", title_style))
        gen_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        elements.append(Paragraph(f"Generated At: {gen_time} | Confidential — Internal Use Only", subtitle_style))
        elements.append(Spacer(1, 10))

        # KPI Summary Table
        kpi_data = [["Metric", "Value"]]
        for k, v in data.items():
            if isinstance(v, (int, float, str)) and k not in ["start_date", "end_date", "granularity"]:
                k_label = k.replace("_", " ").title()
                kpi_data.append([Paragraph(escape_text(k_label), body_style), Paragraph(escape_text(str(v)), body_style)])
            elif isinstance(v, dict) and all(isinstance(val, (int, float, str)) for val in v.values()):
                k_label = k.replace("_", " ").title()
                val_str = ", ".join(f"{curr}: {val}" for curr, val in v.items())
                kpi_data.append([Paragraph(escape_text(k_label), body_style), Paragraph(escape_text(val_str), body_style)])

        if len(kpi_data) > 1:
            t = Table(kpi_data, colWidths=[250, 300])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ]))
            elements.append(Paragraph("Executive Metrics Summary", section_style))
            elements.append(t)
            elements.append(Spacer(1, 15))

        # Customer 360 / Nested Tables
        if "customer" in data and isinstance(data["customer"], dict):
            c_info = data["customer"]
            elements.append(Paragraph(f"Customer Profile: {escape_text(c_info.get('name', ''))} ({escape_text(c_info.get('customer_code', ''))})", section_style))
            p_data = [
                ["Tier", escape_text(c_info.get("customer_tier", "Standard"))],
                ["Sales Rep", escape_text(c_info.get("assigned_sales_rep", "Unassigned"))],
                ["Active Status", "Active" if c_info.get("is_active") else "Inactive"],
            ]
            pt = Table(p_data, colWidths=[150, 300])
            pt.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
            ]))
            elements.append(pt)
            elements.append(Spacer(1, 15))

        # Footer / Page Building
        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
