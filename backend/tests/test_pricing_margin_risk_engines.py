from decimal import Decimal
import pytest

from app.core.enums import RiskLevel, RiskReasonCode
from app.engines.margin import MarginEngine
from app.engines.pricing import PricingEngine
from app.engines.risk import RiskEngine


def test_pricing_engine_sequential_discount():
    # 10% line discount, 5% order discount
    # gross = 100 * 100 = 10,000.00
    # after line discount = 10,000 * 0.90 = 9,000.00
    # after order discount = 9,000 * 0.95 = 8,550.00
    # discount_amount = 10,000 - 8,550 = 1,450.00
    # effective_discount_pct = (1,450 / 10,000) * 100 = 14.50% (NOT 15.00%)
    res = PricingEngine.calculate_line(
        quantity=Decimal("100.000"),
        unit_list_price=Decimal("100.00"),
        line_discount_pct=Decimal("10.00"),
        order_discount_pct=Decimal("5.00"),
    )
    assert res.gross_line_total == Decimal("10000.00")
    assert res.after_line_discount == Decimal("9000.00")
    assert res.net_line_total == Decimal("8550.00")
    assert res.discount_amount == Decimal("1450.00")
    assert res.effective_discount_pct == Decimal("14.50")


def test_pricing_engine_quotation_aggregation():
    line_inputs = [
        {"quantity": Decimal("10"), "unit_list_price": Decimal("100.00"), "line_discount_pct": Decimal("10.00")},
        {"quantity": Decimal("5"), "unit_list_price": Decimal("200.00"), "line_discount_pct": Decimal("0.00")},
    ]
    res = PricingEngine.calculate_quotation(line_inputs, order_discount_pct=Decimal("5.00"))
    # Line 1: gross 1000, after line 900, net 855, disc 145
    # Line 2: gross 1000, after line 1000, net 950, disc 50
    # Subtotal: gross 2000, net 1805, disc 195
    # Weighted eff disc: (195 / 2000) * 100 = 9.75%
    assert res.gross_subtotal == Decimal("2000.00")
    assert res.net_total == Decimal("1805.00")
    assert res.discount_amount == Decimal("195.00")
    assert res.weighted_effective_discount_pct == Decimal("9.75")


def test_margin_engine_calculations():
    # Line net revenue = 855.00, line cost = 10 * 50 = 500.00
    # margin_amount = 355.00, margin_pct = (355 / 855) * 100 = 41.52%
    res = MarginEngine.calculate_line(
        quantity=Decimal("10.000"),
        unit_cost=Decimal("50.00"),
        net_line_total=Decimal("855.00"),
    )
    assert res.line_cost == Decimal("500.00")
    assert res.margin_amount == Decimal("355.00")
    assert res.margin_pct == Decimal("41.52")


def test_margin_engine_zero_revenue_protection():
    res = MarginEngine.calculate_line(
        quantity=Decimal("1.000"),
        unit_cost=Decimal("50.00"),
        net_line_total=Decimal("0.00"),
    )
    assert res.line_cost == Decimal("500.00")
    assert res.margin_amount == Decimal("-500.00")
    assert res.margin_pct == Decimal("-100.00")


def test_risk_engine_line_evaluation_green():
    res = RiskEngine.evaluate_line(
        effective_discount_pct=Decimal("8.00"),
        standard_discount_pct=Decimal("10.00"),
        max_discount_pct=Decimal("20.00"),
        net_line_total=Decimal("920.00"),
        line_cost=Decimal("500.00"),
    )
    assert res.risk_level == RiskLevel.GREEN
    assert res.discount_overage_pct == Decimal("0.00")
    assert len(res.reasons) == 1
    assert res.reasons[0].code == RiskReasonCode.WITHIN_STANDARD_DISCOUNT


def test_risk_engine_line_evaluation_yellow():
    res = RiskEngine.evaluate_line(
        effective_discount_pct=Decimal("15.00"),
        standard_discount_pct=Decimal("10.00"),
        max_discount_pct=Decimal("20.00"),
        net_line_total=Decimal("850.00"),
        line_cost=Decimal("500.00"),
    )
    assert res.risk_level == RiskLevel.YELLOW
    assert res.discount_overage_pct == Decimal("0.00")
    assert res.reasons[0].code == RiskReasonCode.ABOVE_STANDARD_WITHIN_MAX


def test_risk_engine_line_evaluation_coral_red_over_max():
    res = RiskEngine.evaluate_line(
        effective_discount_pct=Decimal("25.00"),
        standard_discount_pct=Decimal("10.00"),
        max_discount_pct=Decimal("20.00"),
        net_line_total=Decimal("750.00"),
        line_cost=Decimal("500.00"),
    )
    assert res.risk_level == RiskLevel.CORAL_RED
    assert res.discount_overage_pct == Decimal("5.00")
    assert res.reasons[0].code == RiskReasonCode.DISCOUNT_ABOVE_MAX


def test_risk_engine_blended_score_and_quote_level():
    # Large line: gross 10,000, eff disc 22%, max 20% -> 2% overage
    # Small line: gross 1,000, eff disc 28%, max 20% -> 8% overage
    # Weighted overage = (10000 * 2 + 1000 * 8) / 11000 = 28000 / 11000 = 2.55%
    line_inputs = [
        {
            "effective_discount_pct": Decimal("22.00"),
            "standard_discount_pct": Decimal("10.00"),
            "max_discount_pct": Decimal("20.00"),
            "net_line_total": Decimal("7800.00"),
            "line_cost": Decimal("4000.00"),
            "gross_line_total": Decimal("10000.00"),
            "id": 1,
        },
        {
            "effective_discount_pct": Decimal("28.00"),
            "standard_discount_pct": Decimal("10.00"),
            "max_discount_pct": Decimal("20.00"),
            "net_line_total": Decimal("720.00"),
            "line_cost": Decimal("400.00"),
            "gross_line_total": Decimal("1000.00"),
            "id": 2,
        },
    ]

    res = RiskEngine.evaluate_quotation(
        line_eval_inputs=line_inputs,
        quote_margin_amount=Decimal("4120.00"),
        net_total=Decimal("8520.00"),
    )
    assert res.blended_risk_score == Decimal("2.55")
    assert res.risk_level == RiskLevel.CORAL_RED
