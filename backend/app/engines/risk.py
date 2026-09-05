from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from pydantic import BaseModel

from app.core.enums import RiskLevel, RiskReasonCode


class RiskReasonItem(BaseModel):
    code: str
    severity: str
    message: str
    actual_value: Optional[Decimal] = None
    threshold_value: Optional[Decimal] = None
    quotation_line_id: Optional[int] = None


class LineRiskResult(BaseModel):
    risk_level: RiskLevel
    discount_overage_pct: Decimal
    reasons: List[RiskReasonItem]


class QuoteRiskResult(BaseModel):
    blended_risk_score: Decimal
    risk_level: RiskLevel
    line_results: List[LineRiskResult]
    reasons: List[RiskReasonItem]


class RiskEngine:
    """Deterministic commercial risk calculation engine."""

    TWOPLACES = Decimal("0.01")

    @classmethod
    def _quantize_pct(cls, pct: Decimal) -> Decimal:
        return pct.quantize(cls.TWOPLACES, rounding=ROUND_HALF_UP)

    @classmethod
    def evaluate_line(
        cls,
        effective_discount_pct: Decimal,
        standard_discount_pct: Optional[Decimal],
        max_discount_pct: Optional[Decimal],
        net_line_total: Decimal,
        line_cost: Decimal,
        line_id: Optional[int] = None,
    ) -> LineRiskResult:
        reasons: List[RiskReasonItem] = []
        risk_level = RiskLevel.GREEN
        overage_pct = Decimal("0.00")

        # 1. Evaluate Margin / Revenue safety first
        if net_line_total < line_cost:
            risk_level = RiskLevel.CORAL_RED
            reasons.append(
                RiskReasonItem(
                    code=RiskReasonCode.NEGATIVE_MARGIN,
                    severity=RiskLevel.CORAL_RED.value,
                    message=f"Line net revenue ({net_line_total}) is below total cost ({line_cost}).",
                    actual_value=net_line_total,
                    threshold_value=line_cost,
                    quotation_line_id=line_id,
                )
            )
        elif net_line_total == Decimal("0") and line_cost > Decimal("0"):
            risk_level = RiskLevel.CORAL_RED
            reasons.append(
                RiskReasonItem(
                    code=RiskReasonCode.ZERO_REVENUE_WITH_COST,
                    severity=RiskLevel.CORAL_RED.value,
                    message=f"Line net revenue is 0 with positive cost ({line_cost}).",
                    actual_value=Decimal("0.00"),
                    threshold_value=line_cost,
                    quotation_line_id=line_id,
                )
            )

        # 2. Evaluate Policy / Discount limits
        if standard_discount_pct is None or max_discount_pct is None:
            if risk_level != RiskLevel.CORAL_RED:
                risk_level = RiskLevel.YELLOW
            reasons.append(
                RiskReasonItem(
                    code=RiskReasonCode.NO_APPLICABLE_DISCOUNT_POLICY,
                    severity=RiskLevel.YELLOW.value,
                    message="No applicable commercial discount policy found for product line.",
                    actual_value=effective_discount_pct,
                    threshold_value=None,
                    quotation_line_id=line_id,
                )
            )
        else:
            if effective_discount_pct <= standard_discount_pct:
                reasons.append(
                    RiskReasonItem(
                        code=RiskReasonCode.WITHIN_STANDARD_DISCOUNT,
                        severity=RiskLevel.GREEN.value,
                        message=f"Effective discount ({effective_discount_pct}%) is within standard policy limit ({standard_discount_pct}%).",
                        actual_value=effective_discount_pct,
                        threshold_value=standard_discount_pct,
                        quotation_line_id=line_id,
                    )
                )
            elif effective_discount_pct <= max_discount_pct:
                if risk_level != RiskLevel.CORAL_RED:
                    risk_level = RiskLevel.YELLOW
                reasons.append(
                    RiskReasonItem(
                        code=RiskReasonCode.ABOVE_STANDARD_WITHIN_MAX,
                        severity=RiskLevel.YELLOW.value,
                        message=f"Effective discount ({effective_discount_pct}%) exceeds standard ({standard_discount_pct}%) but is within max threshold ({max_discount_pct}%).",
                        actual_value=effective_discount_pct,
                        threshold_value=max_discount_pct,
                        quotation_line_id=line_id,
                    )
                )
            else:
                risk_level = RiskLevel.CORAL_RED
                overage_pct = cls._quantize_pct(effective_discount_pct - max_discount_pct)
                reasons.append(
                    RiskReasonItem(
                        code=RiskReasonCode.DISCOUNT_ABOVE_MAX,
                        severity=RiskLevel.CORAL_RED.value,
                        message=f"Effective discount ({effective_discount_pct}%) exceeds maximum allowed policy threshold ({max_discount_pct}%) by {overage_pct}%.",
                        actual_value=effective_discount_pct,
                        threshold_value=max_discount_pct,
                        quotation_line_id=line_id,
                    )
                )

        return LineRiskResult(
            risk_level=risk_level,
            discount_overage_pct=overage_pct,
            reasons=reasons,
        )

    @classmethod
    def evaluate_quotation(
        cls,
        line_eval_inputs: List[dict],
        quote_margin_amount: Decimal,
        net_total: Decimal,
    ) -> QuoteRiskResult:
        line_results: List[LineRiskResult] = []
        all_reasons: List[RiskReasonItem] = []

        weighted_overage_sum = Decimal("0.00")
        total_gross_weight = Decimal("0.00")

        has_coral_red = False
        has_yellow = False

        for inp in line_eval_inputs:
            eff_disc = inp["effective_discount_pct"]
            std_disc = inp.get("standard_discount_pct")
            max_disc = inp.get("max_discount_pct")
            net_line = inp["net_line_total"]
            line_cost = inp["line_cost"]
            gross_line = inp["gross_line_total"]
            line_id = inp.get("id")

            res = cls.evaluate_line(
                effective_discount_pct=eff_disc,
                standard_discount_pct=std_disc,
                max_discount_pct=max_disc,
                net_line_total=net_line,
                line_cost=line_cost,
                line_id=line_id,
            )
            line_results.append(res)
            all_reasons.extend(res.reasons)

            if res.risk_level == RiskLevel.CORAL_RED:
                has_coral_red = True
            elif res.risk_level == RiskLevel.YELLOW:
                has_yellow = True

            # Calculate weighted overage score
            if max_disc is not None and gross_line > Decimal("0"):
                overage = max(eff_disc - max_disc, Decimal("0.00"))
                weighted_overage_sum += gross_line * overage
                total_gross_weight += gross_line

        # Quote-level margin check
        if quote_margin_amount < Decimal("0.00"):
            has_coral_red = True
            all_reasons.append(
                RiskReasonItem(
                    code=RiskReasonCode.NEGATIVE_MARGIN,
                    severity=RiskLevel.CORAL_RED.value,
                    message=f"Overall quotation has a negative margin amount ({quote_margin_amount}).",
                    actual_value=quote_margin_amount,
                    threshold_value=Decimal("0.00"),
                )
            )

        # Blended risk score
        if total_gross_weight > Decimal("0"):
            blended_score = cls._quantize_pct(weighted_overage_sum / total_gross_weight)
        else:
            blended_score = Decimal("0.00")

        # Determine quote risk level
        if has_coral_red:
            quote_risk_level = RiskLevel.CORAL_RED
        elif has_yellow:
            quote_risk_level = RiskLevel.YELLOW
        else:
            quote_risk_level = RiskLevel.GREEN

        return QuoteRiskResult(
            blended_risk_score=blended_score,
            risk_level=quote_risk_level,
            line_results=line_results,
            reasons=all_reasons,
        )
