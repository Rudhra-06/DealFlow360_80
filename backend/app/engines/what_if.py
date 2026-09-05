from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel

from app.engines.approval import ApprovalEngine
from app.engines.margin import MarginEngine
from app.engines.pricing import PricingEngine
from app.engines.risk import RiskEngine


class StateSnapshot(BaseModel):
    gross_subtotal: Decimal
    discount_amount: Decimal
    net_total: Decimal
    total_cost: Decimal
    margin_amount: Decimal
    margin_pct: Decimal
    weighted_effective_discount_pct: Decimal
    blended_risk_score: Decimal
    risk_level: str
    required_approval_roles: List[str]
    projected_status: str


class DeltaMetrics(BaseModel):
    net_total_delta: Decimal
    margin_amount_delta: Decimal
    margin_pct_delta: Decimal
    risk_score_delta: Decimal


class WhatIfSimulationResult(BaseModel):
    quotation_id: int
    persisted: bool = False
    before: StateSnapshot
    after: StateSnapshot
    changes: DeltaMetrics
    new_approval_required: bool
    risk_reasons: List[dict]


class WhatIfSimulatorEngine:
    """Deterministic in-memory non-persistent what-if simulation engine."""

    @classmethod
    def simulate(
        cls,
        quotation_id: int,
        current_order_discount_pct: Decimal,
        current_payment_terms_days: int,
        current_customer_tier_id: Optional[int],
        existing_lines: List[dict],
        active_approval_policies: List[dict],
        order_discount_pct_override: Optional[Decimal] = None,
        payment_terms_days_override: Optional[int] = None,
        line_overrides: Optional[List[dict]] = None,
    ) -> WhatIfSimulationResult:
        line_override_map = {lo["line_id"]: lo for lo in (line_overrides or []) if "line_id" in lo}

        # ----------------------------------------------------
        # 1. Evaluate BEFORE state
        # ----------------------------------------------------
        before_pricing_inputs = []
        before_margin_inputs = []
        before_risk_inputs = []

        for line in existing_lines:
            before_pricing_inputs.append(
                {
                    "quantity": line["quantity"],
                    "unit_list_price": line["unit_list_price"],
                    "line_discount_pct": line["line_discount_pct"],
                }
            )

        before_pricing = PricingEngine.calculate_quotation(
            before_pricing_inputs, current_order_discount_pct
        )

        for idx, line in enumerate(existing_lines):
            lr = before_pricing.line_results[idx]
            before_margin_inputs.append(
                {
                    "quantity": line["quantity"],
                    "unit_cost": line["unit_cost"],
                    "net_line_total": lr.net_line_total,
                }
            )

        before_margin = MarginEngine.calculate_quotation(
            before_margin_inputs, before_pricing.net_total
        )

        has_line_over_max_before = False
        for idx, line in enumerate(existing_lines):
            lr = before_pricing.line_results[idx]
            mr = before_margin.line_results[idx]
            max_disc = line.get("max_discount_pct_snapshot")
            if max_disc is not None and lr.effective_discount_pct > max_disc:
                has_line_over_max_before = True

            before_risk_inputs.append(
                {
                    "id": line.get("id"),
                    "effective_discount_pct": lr.effective_discount_pct,
                    "standard_discount_pct": line.get("standard_discount_pct_snapshot"),
                    "max_discount_pct": max_disc,
                    "net_line_total": lr.net_line_total,
                    "line_cost": mr.line_cost,
                    "gross_line_total": lr.gross_line_total,
                }
            )

        before_risk = RiskEngine.evaluate_quotation(
            before_risk_inputs, before_margin.margin_amount, before_pricing.net_total
        )

        before_approval = ApprovalEngine.evaluate(
            weighted_effective_discount_pct=before_pricing.weighted_effective_discount_pct,
            margin_pct=before_margin.margin_pct,
            payment_terms_days=current_payment_terms_days,
            blended_risk_score=before_risk.blended_risk_score,
            customer_tier_id=current_customer_tier_id,
            has_line_over_max_discount=has_line_over_max_before,
            active_policies=active_approval_policies,
        )

        before_snapshot = StateSnapshot(
            gross_subtotal=before_pricing.gross_subtotal,
            discount_amount=before_pricing.discount_amount,
            net_total=before_pricing.net_total,
            total_cost=before_margin.total_cost,
            margin_amount=before_margin.margin_amount,
            margin_pct=before_margin.margin_pct,
            weighted_effective_discount_pct=before_pricing.weighted_effective_discount_pct,
            blended_risk_score=before_risk.blended_risk_score,
            risk_level=before_risk.risk_level.value,
            required_approval_roles=before_approval.required_roles,
            projected_status=before_approval.projected_status.value,
        )

        # ----------------------------------------------------
        # 2. Evaluate AFTER state (Hypothetical Overrides)
        # ----------------------------------------------------
        sim_order_disc = order_discount_pct_override if order_discount_pct_override is not None else current_order_discount_pct
        sim_terms_days = payment_terms_days_override if payment_terms_days_override is not None else current_payment_terms_days

        after_pricing_inputs = []
        after_margin_inputs = []
        after_risk_inputs = []

        simulated_lines = []
        for line in existing_lines:
            line_copy = dict(line)
            lid = line_copy.get("id")
            if lid in line_override_map:
                override = line_override_map[lid]
                if override.get("quantity") is not None:
                    line_copy["quantity"] = override["quantity"]
                if override.get("line_discount_pct") is not None:
                    line_copy["line_discount_pct"] = override["line_discount_pct"]

            simulated_lines.append(line_copy)
            after_pricing_inputs.append(
                {
                    "quantity": line_copy["quantity"],
                    "unit_list_price": line_copy["unit_list_price"],
                    "line_discount_pct": line_copy["line_discount_pct"],
                }
            )

        after_pricing = PricingEngine.calculate_quotation(after_pricing_inputs, sim_order_disc)

        for idx, line_copy in enumerate(simulated_lines):
            lr = after_pricing.line_results[idx]
            after_margin_inputs.append(
                {
                    "quantity": line_copy["quantity"],
                    "unit_cost": line_copy["unit_cost"],
                    "net_line_total": lr.net_line_total,
                }
            )

        after_margin = MarginEngine.calculate_quotation(after_margin_inputs, after_pricing.net_total)

        has_line_over_max_after = False
        for idx, line_copy in enumerate(simulated_lines):
            lr = after_pricing.line_results[idx]
            mr = after_margin.line_results[idx]
            max_disc = line_copy.get("max_discount_pct_snapshot")
            if max_disc is not None and lr.effective_discount_pct > max_disc:
                has_line_over_max_after = True

            after_risk_inputs.append(
                {
                    "id": line_copy.get("id"),
                    "effective_discount_pct": lr.effective_discount_pct,
                    "standard_discount_pct": line_copy.get("standard_discount_pct_snapshot"),
                    "max_discount_pct": max_disc,
                    "net_line_total": lr.net_line_total,
                    "line_cost": mr.line_cost,
                    "gross_line_total": lr.gross_line_total,
                }
            )

        after_risk = RiskEngine.evaluate_quotation(
            after_risk_inputs, after_margin.margin_amount, after_pricing.net_total
        )

        after_approval = ApprovalEngine.evaluate(
            weighted_effective_discount_pct=after_pricing.weighted_effective_discount_pct,
            margin_pct=after_margin.margin_pct,
            payment_terms_days=sim_terms_days,
            blended_risk_score=after_risk.blended_risk_score,
            customer_tier_id=current_customer_tier_id,
            has_line_over_max_discount=has_line_over_max_after,
            active_policies=active_approval_policies,
        )

        after_snapshot = StateSnapshot(
            gross_subtotal=after_pricing.gross_subtotal,
            discount_amount=after_pricing.discount_amount,
            net_total=after_pricing.net_total,
            total_cost=after_margin.total_cost,
            margin_amount=after_margin.margin_amount,
            margin_pct=after_margin.margin_pct,
            weighted_effective_discount_pct=after_pricing.weighted_effective_discount_pct,
            blended_risk_score=after_risk.blended_risk_score,
            risk_level=after_risk.risk_level.value,
            required_approval_roles=after_approval.required_roles,
            projected_status=after_approval.projected_status.value,
        )

        # ----------------------------------------------------
        # 3. Deltas & Projected Impact
        # ----------------------------------------------------
        deltas = DeltaMetrics(
            net_total_delta=after_snapshot.net_total - before_snapshot.net_total,
            margin_amount_delta=after_snapshot.margin_amount - before_snapshot.margin_amount,
            margin_pct_delta=after_snapshot.margin_pct - before_snapshot.margin_pct,
            risk_score_delta=after_snapshot.blended_risk_score - before_snapshot.blended_risk_score,
        )

        new_approval_req = len(after_approval.required_roles) > len(before_approval.required_roles)

        risk_reasons_out = [
            {
                "code": r.code,
                "severity": r.severity,
                "message": r.message,
                "actual_value": str(r.actual_value) if r.actual_value is not None else None,
                "threshold_value": str(r.threshold_value) if r.threshold_value is not None else None,
            }
            for r in after_risk.reasons
        ]

        return WhatIfSimulationResult(
            quotation_id=quotation_id,
            persisted=False,
            before=before_snapshot,
            after=after_snapshot,
            changes=deltas,
            new_approval_required=new_approval_req,
            risk_reasons=risk_reasons_out,
        )
