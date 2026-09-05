import pytest
from datetime import datetime, timezone
from decimal import Decimal
from app.engines.proration import ProrationEngine


def test_proration_engine_daily():
    engine = ProrationEngine()

    start = datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 3, 31, 0, 0, 0, tzinfo=timezone.utc)
    effective = datetime(2026, 3, 16, 0, 0, 0, tzinfo=timezone.utc)

    res = engine.calculate_mid_cycle_proration(
        period_start=start,
        period_end=end,
        effective_date=effective,
        old_quantity=Decimal("10"),
        new_quantity=Decimal("15"),
        unit_price=Decimal("100.00"),
        proration_method="DAILY",
    )

    # 30 total days between March 1 and March 31.
    # 15 remaining days (March 16 to March 31).
    # Delta quantity = +5. Total unit price = 100.00. Total monthly delta = 500.00.
    # Fraction = 15/30 = 0.500000. Prorated = 250.00.
    assert res.prorated_amount == Decimal("250.00")
    assert res.period_days == 30
    assert res.remaining_days == 15


def test_proration_engine_no_proration():
    engine = ProrationEngine()

    start = datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 3, 31, 0, 0, 0, tzinfo=timezone.utc)
    effective = datetime(2026, 3, 16, 0, 0, 0, tzinfo=timezone.utc)

    res = engine.calculate_mid_cycle_proration(
        period_start=start,
        period_end=end,
        effective_date=effective,
        old_quantity=Decimal("10"),
        new_quantity=Decimal("15"),
        unit_price=Decimal("100.00"),
        proration_method="NONE",
    )

    assert res.prorated_amount == Decimal("0.00")
