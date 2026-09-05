from decimal import Decimal
import pytest

from app.core.enums import QuotationStatus, RoleName
from app.engines.approval import ApprovalEngine


def test_approval_engine_no_approval_required():
    res = ApprovalEngine.evaluate(
        weighted_effective_discount_pct=Decimal("5.00"),
        margin_pct=Decimal("30.00"),
        payment_terms_days=30,
        blended_risk_score=Decimal("0.00"),
        customer_tier_id=1,
        has_line_over_max_discount=False,
        active_policies=[
            {
                "id": 1,
                "customer_tier_id": None,
                "discount_above_pct": Decimal("10.00"),
                "margin_below_pct": None,
                "payment_terms_above_days": None,
                "blended_risk_above": None,
                "approval_role": RoleName.SALES_MANAGER.value,
            }
        ],
    )
    assert res.requires_approval is False
    assert res.projected_status == QuotationStatus.APPROVED
    assert len(res.required_roles) == 0


def test_approval_engine_sales_manager_trigger():
    res = ApprovalEngine.evaluate(
        weighted_effective_discount_pct=Decimal("15.00"),
        margin_pct=Decimal("30.00"),
        payment_terms_days=30,
        blended_risk_score=Decimal("0.00"),
        customer_tier_id=1,
        has_line_over_max_discount=False,
        active_policies=[
            {
                "id": 1,
                "customer_tier_id": None,
                "discount_above_pct": Decimal("10.00"),
                "margin_below_pct": None,
                "payment_terms_above_days": None,
                "blended_risk_above": None,
                "approval_role": RoleName.SALES_MANAGER.value,
            }
        ],
    )
    assert res.requires_approval is True
    assert res.projected_status == QuotationStatus.PENDING_MANAGER_APPROVAL
    assert res.required_roles == [RoleName.SALES_MANAGER.value]
    assert len(res.triggers) == 1
    assert res.triggers[0].trigger_code == "DISCOUNT_THRESHOLD"


def test_approval_engine_finance_two_level_chain():
    res = ApprovalEngine.evaluate(
        weighted_effective_discount_pct=Decimal("25.00"),
        margin_pct=Decimal("8.00"),
        payment_terms_days=60,
        blended_risk_score=Decimal("5.00"),
        customer_tier_id=1,
        has_line_over_max_discount=False,
        active_policies=[
            {
                "id": 1,
                "customer_tier_id": None,
                "discount_above_pct": Decimal("20.00"),
                "margin_below_pct": Decimal("10.00"),
                "payment_terms_above_days": Decimal("45.00"),
                "blended_risk_above": None,
                "approval_role": RoleName.FINANCE_OPERATIONS.value,
            }
        ],
    )
    assert res.requires_approval is True
    # Finance requirement forces 2-level chain: Sales Manager -> Finance Operations
    assert res.required_roles == [RoleName.SALES_MANAGER.value, RoleName.FINANCE_OPERATIONS.value]
    assert res.projected_status == QuotationStatus.PENDING_MANAGER_APPROVAL


def test_approval_engine_blended_risk_trigger():
    res = ApprovalEngine.evaluate(
        weighted_effective_discount_pct=Decimal("8.00"),
        margin_pct=Decimal("25.00"),
        payment_terms_days=30,
        blended_risk_score=Decimal("4.50"),
        customer_tier_id=1,
        has_line_over_max_discount=False,
        active_policies=[
            {
                "id": 10,
                "customer_tier_id": None,
                "discount_above_pct": None,
                "margin_below_pct": None,
                "payment_terms_above_days": None,
                "blended_risk_above": Decimal("3.00"),
                "approval_role": RoleName.SALES_MANAGER.value,
            }
        ],
    )
    assert res.requires_approval is True
    assert res.triggers[0].trigger_code == "BLENDED_RISK_THRESHOLD"
    assert res.triggers[0].actual_value == Decimal("4.50")
