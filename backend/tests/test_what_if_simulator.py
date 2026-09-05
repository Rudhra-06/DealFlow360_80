from decimal import Decimal
import pytest

from app.engines.what_if import WhatIfSimulatorEngine


def test_what_if_simulation_non_persistence():
    existing_lines = [
        {
            "id": 1,
            "product_id": 101,
            "quantity": Decimal("10.000"),
            "unit_list_price": Decimal("100.00"),
            "unit_cost": Decimal("60.00"),
            "line_discount_pct": Decimal("10.00"),
            "standard_discount_pct_snapshot": Decimal("10.00"),
            "max_discount_pct_snapshot": Decimal("20.00"),
        }
    ]
    active_policies = [
        {
            "id": 1,
            "customer_tier_id": None,
            "discount_above_pct": Decimal("15.00"),
            "margin_below_pct": None,
            "payment_terms_above_days": None,
            "blended_risk_above": None,
            "approval_role": "SALES_MANAGER",
        }
    ]

    res = WhatIfSimulatorEngine.simulate(
        quotation_id=1,
        current_order_discount_pct=Decimal("0.00"),
        current_payment_terms_days=30,
        current_customer_tier_id=1,
        existing_lines=existing_lines,
        active_approval_policies=active_policies,
        order_discount_pct_override=Decimal("10.00"),  # Simulated order discount = 10%
    )

    assert res.persisted is False
    assert res.before.net_total == Decimal("900.00")
    assert res.after.net_total == Decimal("810.00")  # 900 * 0.90
    assert res.changes.net_total_delta == Decimal("-90.00")
    assert res.before.weighted_effective_discount_pct == Decimal("10.00")
    assert res.after.weighted_effective_discount_pct == Decimal("19.00")  # 1 - 0.90 * 0.90 = 19%
    assert res.after.projected_status == "PENDING_MANAGER_APPROVAL"
    assert res.new_approval_required is True
