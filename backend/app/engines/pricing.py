from decimal import Decimal, ROUND_HALF_UP
from typing import List
from pydantic import BaseModel


class LinePricingResult(BaseModel):
    gross_line_total: Decimal
    after_line_discount: Decimal
    net_line_total: Decimal
    discount_amount: Decimal
    effective_discount_pct: Decimal


class QuotePricingResult(BaseModel):
    gross_subtotal: Decimal
    discount_amount: Decimal
    net_total: Decimal
    weighted_effective_discount_pct: Decimal
    line_results: List[LinePricingResult]


class PricingEngine:
    """Deterministic, side-effect free commercial pricing calculation engine."""

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
        unit_list_price: Decimal,
        line_discount_pct: Decimal,
        order_discount_pct: Decimal,
    ) -> LinePricingResult:
        if quantity <= Decimal("0"):
            raise ValueError("Quantity must be greater than zero.")

        gross = cls._quantize_money(quantity * unit_list_price)
        
        # Sequential discount math: gross * (1 - line_disc/100) * (1 - order_disc/100)
        line_factor = Decimal("1") - (line_discount_pct / Decimal("100"))
        after_line = gross * line_factor
        
        order_factor = Decimal("1") - (order_discount_pct / Decimal("100"))
        net = cls._quantize_money(after_line * order_factor)

        discount_amt = gross - net

        if gross > Decimal("0"):
            effective_pct = cls._quantize_pct((discount_amt / gross) * Decimal("100"))
        else:
            effective_pct = Decimal("0.00")

        return LinePricingResult(
            gross_line_total=gross,
            after_line_discount=cls._quantize_money(after_line),
            net_line_total=net,
            discount_amount=discount_amt,
            effective_discount_pct=effective_pct,
        )

    @classmethod
    def calculate_quotation(
        cls,
        line_inputs: List[dict],
        order_discount_pct: Decimal,
    ) -> QuotePricingResult:
        line_results = []
        gross_subtotal = Decimal("0.00")
        net_total = Decimal("0.00")
        total_discount_amount = Decimal("0.00")

        for inp in line_inputs:
            res = cls.calculate_line(
                quantity=inp["quantity"],
                unit_list_price=inp["unit_list_price"],
                line_discount_pct=inp["line_discount_pct"],
                order_discount_pct=order_discount_pct,
            )
            line_results.append(res)
            gross_subtotal += res.gross_line_total
            net_total += res.net_line_total
            total_discount_amount += res.discount_amount

        gross_subtotal = cls._quantize_money(gross_subtotal)
        net_total = cls._quantize_money(net_total)
        total_discount_amount = cls._quantize_money(total_discount_amount)

        if gross_subtotal > Decimal("0"):
            weighted_eff_pct = cls._quantize_pct(
                ((gross_subtotal - net_total) / gross_subtotal) * Decimal("100")
            )
        else:
            weighted_eff_pct = Decimal("0.00")

        return QuotePricingResult(
            gross_subtotal=gross_subtotal,
            discount_amount=total_discount_amount,
            net_total=net_total,
            weighted_effective_discount_pct=weighted_eff_pct,
            line_results=line_results,
        )
