from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class ProrationCalculationResult:
    proration_fraction: Decimal
    period_days: int
    remaining_days: int
    delta_quantity: Decimal
    unit_price: Decimal
    prorated_amount: Decimal  # Positive for charge, negative for credit
    explanation: str


class ProrationEngine:
    """
    Deterministic side-effect free proration engine.
    Calculates exact daily proration fractions for mid-cycle quantity modifications and cancellations.
    Formula:
      period_days = (period_end - period_start).days
      remaining_days = (period_end - effective_date).days
      proration_fraction = remaining_days / period_days
      prorated_amount = delta_quantity * unit_price * proration_fraction
    """

    @staticmethod
    def calculate_mid_cycle_proration(
        period_start: datetime,
        period_end: datetime,
        effective_date: datetime,
        old_quantity: Decimal,
        new_quantity: Decimal,
        unit_price: Decimal,
        proration_method: str = "DAILY",
    ) -> ProrationCalculationResult:
        delta_qty = new_quantity - old_quantity

        if proration_method != "DAILY":
            return ProrationCalculationResult(
                proration_fraction=Decimal("0.0000"),
                period_days=(period_end - period_start).days,
                remaining_days=0,
                delta_quantity=delta_qty,
                unit_price=unit_price,
                prorated_amount=Decimal("0.00"),
                explanation=f"Proration method '{proration_method}' evaluates to 0.00 mid-cycle charge.",
            )

        # Sanity check date ordering
        eff = max(period_start, min(effective_date, period_end))

        total_seconds = (period_end - period_start).total_seconds()
        remaining_seconds = (period_end - eff).total_seconds()

        if total_seconds <= 0:
            return ProrationCalculationResult(
                proration_fraction=Decimal("0.0000"),
                period_days=0,
                remaining_days=0,
                delta_quantity=delta_qty,
                unit_price=unit_price,
                prorated_amount=Decimal("0.00"),
                explanation="Invalid period duration.",
            )

        period_days = max(1, (period_end.date() - period_start.date()).days)
        remaining_days = max(0, (period_end.date() - eff.date()).days)

        fraction = (Decimal(str(remaining_seconds)) / Decimal(str(total_seconds))).quantize(
            Decimal("0.000001"), rounding=ROUND_HALF_UP
        )

        raw_amount = delta_qty * unit_price * fraction
        prorated_amount = raw_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        action = "charge" if prorated_amount >= Decimal("0.00") else "credit"
        explanation = (
            f"Prorated {action} of {abs(prorated_amount)} for quantity change from {old_quantity} to {new_quantity} "
            f"across {remaining_days}/{period_days} remaining period days."
        )

        return ProrationCalculationResult(
            proration_fraction=fraction,
            period_days=period_days,
            remaining_days=remaining_days,
            delta_quantity=delta_qty,
            unit_price=unit_price,
            prorated_amount=prorated_amount,
            explanation=explanation,
        )

    @staticmethod
    def calculate_cancellation_credit(
        period_start: datetime,
        period_end: datetime,
        effective_date: datetime,
        current_quantity: Decimal,
        unit_price: Decimal,
        cancellation_method: str = "END_OF_PERIOD",
    ) -> ProrationCalculationResult:
        if cancellation_method == "END_OF_PERIOD":
            return ProrationCalculationResult(
                proration_fraction=Decimal("0.0000"),
                period_days=(period_end - period_start).days,
                remaining_days=0,
                delta_quantity=-current_quantity,
                unit_price=unit_price,
                prorated_amount=Decimal("0.00"),
                explanation="Cancellation at period end generates 0.00 immediate credit note.",
            )

        res = ProrationEngine.calculate_mid_cycle_proration(
            period_start=period_start,
            period_end=period_end,
            effective_date=effective_date,
            old_quantity=current_quantity,
            new_quantity=Decimal("0.0000"),
            unit_price=unit_price,
            proration_method="DAILY",
        )

        credit_amount = abs(res.prorated_amount)
        res.prorated_amount = credit_amount
        res.explanation = f"Immediate cancellation credit of {credit_amount} issued for {res.remaining_days}/{res.period_days} unused days."
        return res
