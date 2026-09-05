from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.margin import MarginEngine
from app.engines.pricing import PricingEngine
from app.engines.risk import RiskEngine
from app.models.quote_risk_reason import QuoteRiskReason
from app.models.quotation import Quotation
from app.models.quotation_line import QuoteLine
from app.repositories.quote_risk_reason import QuoteRiskReasonRepository
from app.services.discount_policy import DiscountPolicyService


class QuotationEvaluationService:
    """Orchestration service for calculating quotation pricing, margin, risk, and policies."""

    def __init__(self, db: AsyncSession) -> None:
        self.db: AsyncSession = db
        self.discount_policy_service = DiscountPolicyService(db)
        self.risk_reason_repo = QuoteRiskReasonRepository()

    async def evaluate_and_update(self, quotation: Quotation) -> Quotation:
        customer_tier_id = quotation.customer.tier_id if quotation.customer else None
        as_of = quotation.created_at or datetime.now(timezone.utc)

        pricing_line_inputs = []
        margin_line_inputs = []

        # 1. Resolve policies & snapshots for each quote line
        for line in quotation.lines:
            policy = await self.discount_policy_service.get_applicable_policy(
                customer_tier_id=customer_tier_id,
                product_id=line.product_id,
                as_of=as_of,
            )

            if policy:
                line.resolved_discount_policy_id = policy.id
                line.standard_discount_pct_snapshot = policy.standard_discount_pct
                line.max_discount_pct_snapshot = policy.max_discount_pct
            else:
                line.resolved_discount_policy_id = None
                line.standard_discount_pct_snapshot = None
                line.max_discount_pct_snapshot = None

            # Prepare pricing engine inputs
            pricing_line_inputs.append(
                {
                    "quantity": line.quantity,
                    "unit_list_price": line.unit_list_price,
                    "line_discount_pct": line.line_discount_pct,
                }
            )

        # 2. Run Pricing Engine
        pricing_res = PricingEngine.calculate_quotation(
            line_inputs=pricing_line_inputs,
            order_discount_pct=quotation.order_discount_pct,
        )

        quotation.gross_subtotal = pricing_res.gross_subtotal
        quotation.discount_amount = pricing_res.discount_amount
        quotation.net_total = pricing_res.net_total
        quotation.weighted_effective_discount_pct = pricing_res.weighted_effective_discount_pct

        # Apply pricing results to lines
        for idx, line in enumerate(quotation.lines):
            lr = pricing_res.line_results[idx]
            line.gross_line_total = lr.gross_line_total
            line.discount_amount = lr.discount_amount
            line.net_line_total = lr.net_line_total
            line.effective_discount_pct = lr.effective_discount_pct

            margin_line_inputs.append(
                {
                    "quantity": line.quantity,
                    "unit_cost": line.unit_cost,
                    "net_line_total": line.net_line_total,
                }
            )

        # 3. Run Margin Engine
        margin_res = MarginEngine.calculate_quotation(
            line_inputs=margin_line_inputs,
            net_total=quotation.net_total,
        )

        quotation.total_cost = margin_res.total_cost
        quotation.margin_amount = margin_res.margin_amount
        quotation.margin_pct = margin_res.margin_pct

        # Apply margin results to lines
        risk_eval_inputs = []
        for idx, line in enumerate(quotation.lines):
            mr = margin_res.line_results[idx]
            line.line_cost = mr.line_cost
            line.margin_amount = mr.margin_amount
            line.margin_pct = mr.margin_pct

            risk_eval_inputs.append(
                {
                    "id": line.id,
                    "effective_discount_pct": line.effective_discount_pct,
                    "standard_discount_pct": line.standard_discount_pct_snapshot,
                    "max_discount_pct": line.max_discount_pct_snapshot,
                    "net_line_total": line.net_line_total,
                    "line_cost": line.line_cost,
                    "gross_line_total": line.gross_line_total,
                }
            )

        # 4. Run Risk Engine
        risk_res = RiskEngine.evaluate_quotation(
            line_eval_inputs=risk_eval_inputs,
            quote_margin_amount=quotation.margin_amount,
            net_total=quotation.net_total,
        )

        quotation.blended_risk_score = risk_res.blended_risk_score
        quotation.risk_level = risk_res.risk_level.value

        # Apply line risk results & build QuoteRiskReason entities
        new_risk_reasons: List[QuoteRiskReason] = []
        for idx, line in enumerate(quotation.lines):
            lrisk = risk_res.line_results[idx]
            line.risk_level = lrisk.risk_level.value
            line.discount_overage_pct = lrisk.discount_overage_pct

        for item in risk_res.reasons:
            new_risk_reasons.append(
                QuoteRiskReason(
                    quotation_id=quotation.id,
                    quotation_line_id=item.quotation_line_id,
                    code=item.code,
                    severity=item.severity,
                    message=item.message,
                    actual_value=item.actual_value,
                    threshold_value=item.threshold_value,
                )
            )

        # 5. Transactionally replace risk reasons
        if quotation.id:
            await self.risk_reason_repo.replace_reasons_for_quotation(
                self.db, quotation.id, new_risk_reasons
            )
        else:
            quotation.risk_reasons = new_risk_reasons

        await self.db.flush()
        return quotation
