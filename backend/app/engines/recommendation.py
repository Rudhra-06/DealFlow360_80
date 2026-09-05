from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Set
from pydantic import BaseModel

from app.engines.margin import MarginEngine
from app.engines.pricing import PricingEngine


class RecommendationCandidate(BaseModel):
    rule_id: int
    source_product_id: int
    suggested_product_id: int
    recommended_qty: Decimal
    standard_discount_used: Decimal
    unit_list_price: Decimal
    unit_cost: Decimal

    incremental_revenue: Decimal
    incremental_cost: Decimal
    incremental_margin_amount: Decimal
    incremental_margin_pct: Decimal

    projected_quote_net_total: Decimal
    projected_quote_margin_pct: Decimal

    is_promoted: bool
    promotion_label: Optional[str] = None
    affinity_score: Decimal
    priority: int
    explanation: str


class RecommendationEngine:
    """Deterministic upsell/cross-sell recommendation evaluation engine."""

    TWOPLACES = Decimal("0.01")

    @classmethod
    def _quantize_pct(cls, pct: Decimal) -> Decimal:
        return pct.quantize(cls.TWOPLACES, rounding=ROUND_HALF_UP)

    @classmethod
    def evaluate(
        cls,
        current_product_ids: Set[int],
        current_order_discount_pct: Decimal,
        current_quote_net_total: Decimal,
        current_quote_total_cost: Decimal,
        dismissed_rule_ids: Set[int],
        active_rules: List[dict],
        products_by_id: dict,
        resolved_policy_discounts: dict,
    ) -> List[RecommendationCandidate]:
        candidates: List[RecommendationCandidate] = []

        for rule in active_rules:
            rule_id = rule["id"]
            source_id = rule["source_product_id"]
            suggested_id = rule["suggested_product_id"]

            # Exclusion checks
            if source_id not in current_product_ids:
                continue
            if suggested_id in current_product_ids:
                continue
            if rule_id in dismissed_rule_ids:
                continue

            suggested_prod = products_by_id.get(suggested_id)
            source_prod = products_by_id.get(source_id)
            if not suggested_prod or not source_prod:
                continue
            if not suggested_prod.get("is_active", True) or not source_prod.get("is_active", True):
                continue

            # Pricing & Margin calculation
            qty = Decimal(str(rule["recommended_qty"]))
            unit_price = Decimal(str(suggested_prod["list_price"]))
            unit_cost = Decimal(str(suggested_prod["cost_price"]))

            std_disc = resolved_policy_discounts.get(suggested_id, Decimal("0.00"))

            line_pricing = PricingEngine.calculate_line(
                quantity=qty,
                unit_list_price=unit_price,
                line_discount_pct=std_disc,
                order_discount_pct=current_order_discount_pct,
            )

            line_margin = MarginEngine.calculate_line(
                quantity=qty,
                unit_cost=unit_cost,
                net_line_total=line_pricing.net_line_total,
            )

            # Server-Side Minimum Margin Filter
            min_margin = rule.get("min_margin_pct")
            if min_margin is not None:
                if line_margin.margin_pct < Decimal(str(min_margin)):
                    continue  # Filter out unsafe suggestion below min_margin_pct

            # Projected Quotation Impact
            projected_net = current_quote_net_total + line_pricing.net_line_total
            projected_cost = current_quote_total_cost + line_margin.line_cost
            projected_margin_amt = projected_net - projected_cost
            if projected_net > Decimal("0"):
                projected_margin_pct = cls._quantize_pct((projected_margin_amt / projected_net) * Decimal("100"))
            else:
                projected_margin_pct = Decimal("0.00")

            explanation = (
                f"Frequently bought with {source_prod.get('name', 'selected item')}. "
                f"Adds {line_pricing.net_line_total} revenue with {line_margin.margin_pct}% margin."
            )

            candidates.append(
                RecommendationCandidate(
                    rule_id=rule_id,
                    source_product_id=source_id,
                    suggested_product_id=suggested_id,
                    recommended_qty=qty,
                    standard_discount_used=std_disc,
                    unit_list_price=unit_price,
                    unit_cost=unit_cost,
                    incremental_revenue=line_pricing.net_line_total,
                    incremental_cost=line_margin.line_cost,
                    incremental_margin_amount=line_margin.margin_amount,
                    incremental_margin_pct=line_margin.margin_pct,
                    projected_quote_net_total=projected_net,
                    projected_quote_margin_pct=projected_margin_pct,
                    is_promoted=rule.get("is_promoted", False),
                    promotion_label=rule.get("promotion_label"),
                    affinity_score=Decimal(str(rule.get("affinity_score", "1.00"))),
                    priority=rule.get("priority", 100),
                    explanation=explanation,
                )
            )

        # Deterministic Ranking: is_promoted DESC, affinity_score DESC, priority ASC, incremental_margin_amount DESC
        candidates.sort(
            key=lambda c: (
                0 if c.is_promoted else 1,
                -c.affinity_score,
                c.priority,
                -c.incremental_margin_amount,
                c.suggested_product_id,
            )
        )

        return candidates
