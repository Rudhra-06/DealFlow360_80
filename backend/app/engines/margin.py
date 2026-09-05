from decimal import Decimal, ROUND_HALF_UP
from typing import List
from pydantic import BaseModel


class LineMarginResult(BaseModel):
    line_cost: Decimal
    margin_amount: Decimal
    margin_pct: Decimal


class QuoteMarginResult(BaseModel):
    total_cost: Decimal
    margin_amount: Decimal
    margin_pct: Decimal
    line_results: List[LineMarginResult]


class MarginEngine:
    """Deterministic, side-effect free commercial margin calculation engine."""

    TWOPLACES = Decimal("0.01")

    @classmethod
    def _quantize_money(cls, amount: Decimal) -> Decimal:
        return amount.quantize(cls.TWOPLACES, rounding=ROUND_HALF_UP)

    @classmethod
    def _quantize_pct(cls, pct: Decimal) -> Decimal:
        return pct.quantize(cls.TWOPLACES, rounding=ROUND_HALF_UP)

    @classmethod
    def calculate_line(
        cls,
        quantity: Decimal,
        unit_cost: Decimal,
        net_line_total: Decimal,
    ) -> LineMarginResult:
        line_cost = cls._quantize_money(quantity * unit_cost)
        margin_amt = net_line_total - line_cost

        if net_line_total > Decimal("0"):
            margin_pct = cls._quantize_pct((margin_amt / net_line_total) * Decimal("100"))
        elif net_line_total == Decimal("0") and line_cost > Decimal("0"):
            margin_pct = Decimal("-100.00")
        else:
            margin_pct = Decimal("0.00")

        return LineMarginResult(
            line_cost=line_cost,
            margin_amount=margin_amt,
            margin_pct=margin_pct,
        )

    @classmethod
    def calculate_quotation(
        cls,
        line_inputs: List[dict],
        net_total: Decimal,
    ) -> QuoteMarginResult:
        line_results = []
        total_cost = Decimal("0.00")

        for inp in line_inputs:
            res = cls.calculate_line(
                quantity=inp["quantity"],
                unit_cost=inp["unit_cost"],
                net_line_total=inp["net_line_total"],
            )
            line_results.append(res)
            total_cost += res.line_cost

        total_cost = cls._quantize_money(total_cost)
        margin_amt = net_total - total_cost

        if net_total > Decimal("0"):
            margin_pct = cls._quantize_pct((margin_amt / net_total) * Decimal("100"))
        elif net_total == Decimal("0") and total_cost > Decimal("0"):
            margin_pct = Decimal("-100.00")
        else:
            margin_pct = Decimal("0.00")

        return QuoteMarginResult(
            total_cost=total_cost,
            margin_amount=margin_amt,
            margin_pct=margin_pct,
            line_results=line_results,
        )
