from decimal import Decimal
import pytest

from app.engines.recommendation import RecommendationEngine


def test_recommendation_engine_filtering_and_ranking():
    current_product_ids = {101}
    dismissed_rule_ids = set()
    active_rules = [
        {
            "id": 1,
            "source_product_id": 101,
            "suggested_product_id": 201,
            "affinity_score": Decimal("2.50"),
            "recommended_qty": Decimal("1.000"),
            "is_promoted": False,
            "promotion_label": None,
            "min_margin_pct": Decimal("15.00"),
            "priority": 10,
        },
        {
            "id": 2,
            "source_product_id": 101,
            "suggested_product_id": 202,
            "affinity_score": Decimal("1.00"),
            "recommended_qty": Decimal("2.000"),
            "is_promoted": True,
            "promotion_label": "Featured Accessory",
            "min_margin_pct": Decimal("10.00"),
            "priority": 100,
        },
        # Unsafe low margin rule (min_margin = 40%) -> should be filtered out!
        {
            "id": 3,
            "source_product_id": 101,
            "suggested_product_id": 203,
            "affinity_score": Decimal("5.00"),
            "recommended_qty": Decimal("1.000"),
            "is_promoted": False,
            "promotion_label": None,
            "min_margin_pct": Decimal("40.00"),
            "priority": 1,
        },
    ]

    products_by_id = {
        101: {"list_price": Decimal("500.00"), "cost_price": Decimal("300.00"), "is_active": True, "name": "Laptop"},
        201: {"list_price": Decimal("100.00"), "cost_price": Decimal("60.00"), "is_active": True, "name": "Mouse"},  # 40% margin
        202: {"list_price": Decimal("50.00"), "cost_price": Decimal("35.00"), "is_active": True, "name": "Pad"},     # 30% margin
        203: {"list_price": Decimal("200.00"), "cost_price": Decimal("150.00"), "is_active": True, "name": "Dock"}, # 25% margin (< 40% min)
    }

    candidates = RecommendationEngine.evaluate(
        current_product_ids=current_product_ids,
        current_order_discount_pct=Decimal("0.00"),
        current_quote_net_total=Decimal("500.00"),
        current_quote_total_cost=Decimal("300.00"),
        dismissed_rule_ids=dismissed_rule_ids,
        active_rules=active_rules,
        products_by_id=products_by_id,
        resolved_policy_discounts={},
    )

    # Candidate 203 filtered out due to min_margin_pct!
    assert len(candidates) == 2
    # Candidate 202 is promoted -> ranked first!
    assert candidates[0].suggested_product_id == 202
    assert candidates[0].is_promoted is True
    assert candidates[1].suggested_product_id == 201
