from typing import Any, Dict, List
from app.models.quote_version import QuoteVersion
from app.models.quote_version_line import QuoteVersionLine
from app.schemas.quote_version import QuoteVersionCompareResult, VersionDiffChange, VersionLineDiff


class VersionDiffEngine:
    """Side-effect free engine for computing deterministic diffs between two quote version snapshots."""

    QUOTE_COMPARE_FIELDS = [
        ("payment_terms_days", "Payment Terms (Days)"),
        ("order_discount_pct", "Order Discount %"),
        ("gross_subtotal", "Gross Subtotal"),
        ("discount_amount", "Discount Amount"),
        ("net_total", "Net Total"),
        ("total_cost", "Total Cost"),
        ("margin_amount", "Margin Amount"),
        ("margin_pct", "Margin %"),
        ("blended_risk_score", "Blended Risk Score"),
        ("risk_level", "Risk Level"),
    ]

    LINE_COMPARE_FIELDS = [
        ("quantity", "Quantity"),
        ("unit_list_price", "Unit List Price"),
        ("line_discount_pct", "Line Discount %"),
        ("effective_discount_pct", "Effective Discount %"),
        ("net_line_total", "Net Line Total"),
        ("margin_amount", "Margin Amount"),
        ("margin_pct", "Margin %"),
        ("billing_plan_id", "Billing Plan ID"),
    ]

    @classmethod
    def compare_versions(cls, v_from: QuoteVersion, v_to: QuoteVersion) -> QuoteVersionCompareResult:
        quote_changes: List[VersionDiffChange] = []

        for field_attr, field_label in cls.QUOTE_COMPARE_FIELDS:
            val_from = getattr(v_from, field_attr, None)
            val_to = getattr(v_to, field_attr, None)
            if val_from != val_to:
                quote_changes.append(
                    VersionDiffChange(
                        field_name=field_label,
                        from_value=val_from,
                        to_value=val_to,
                    )
                )

        # Match lines by product_sku_snapshot or product_id
        lines_from_map: Dict[str, QuoteVersionLine] = {}
        for l in v_from.lines:
            key = l.product_sku_snapshot or f"line-{l.id}"
            lines_from_map[key] = l

        lines_to_map: Dict[str, QuoteVersionLine] = {}
        for l in v_to.lines:
            key = l.product_sku_snapshot or f"line-{l.id}"
            lines_to_map[key] = l

        lines_added: List[Dict[str, Any]] = []
        lines_removed: List[Dict[str, Any]] = []
        lines_changed: List[VersionLineDiff] = []

        # Find added and changed lines
        for key, line_to in lines_to_map.items():
            if key not in lines_from_map:
                lines_added.append(
                    {
                        "product_sku": line_to.product_sku_snapshot,
                        "product_name": line_to.product_name_snapshot,
                        "product_sku_snapshot": line_to.product_sku_snapshot,
                        "product_name_snapshot": line_to.product_name_snapshot,
                        "quantity": str(line_to.quantity),
                        "unit_list_price": str(line_to.unit_list_price),
                        "line_discount_pct": str(line_to.line_discount_pct),
                        "net_line_total": str(line_to.net_line_total),
                    }
                )
            else:
                line_from = lines_from_map[key]
                line_diffs: List[VersionDiffChange] = []
                for field_attr, field_label in cls.LINE_COMPARE_FIELDS:
                    lf_val = getattr(line_from, field_attr, None)
                    lt_val = getattr(line_to, field_attr, None)
                    if lf_val != lt_val:
                        line_diffs.append(
                            VersionDiffChange(
                                field_name=field_label,
                                from_value=lf_val,
                                to_value=lt_val,
                            )
                        )
                if line_diffs:
                    lines_changed.append(
                        VersionLineDiff(
                            product_sku=line_to.product_sku_snapshot,
                            product_name=line_to.product_name_snapshot,
                            change_type="MODIFIED",
                            changes=line_diffs,
                        )
                    )

        # Find removed lines
        for key, line_from in lines_from_map.items():
            if key not in lines_to_map:
                lines_removed.append(
                    {
                        "product_sku": line_from.product_sku_snapshot,
                        "product_name": line_from.product_name_snapshot,
                        "product_sku_snapshot": line_from.product_sku_snapshot,
                        "product_name_snapshot": line_from.product_name_snapshot,
                        "quantity": str(line_from.quantity),
                        "unit_list_price": str(line_from.unit_list_price),
                        "line_discount_pct": str(line_from.line_discount_pct),
                        "net_line_total": str(line_from.net_line_total),
                    }
                )

        return QuoteVersionCompareResult(
            from_version=v_from.version_number,
            to_version=v_to.version_number,
            quote_changes=quote_changes,
            lines_added=lines_added,
            lines_removed=lines_removed,
            lines_changed=lines_changed,
        )
