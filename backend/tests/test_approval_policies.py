import sys
import uuid
from decimal import Decimal
from pathlib import Path
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.roles import RoleName
from app.repositories.customer_tier import CustomerTierRepository
from app.schemas.approval_policy import ApprovalPolicyCreate, ApprovalPolicyUpdate
from app.schemas.customer_tier import CustomerTierCreate
from app.services.approval_policy import ApprovalPolicyService
from app.services.exceptions import CommercialPolicyValidationError


@pytest.mark.anyio
async def test_approval_policy_creation_success(db_session: AsyncSession):
    """Verify creation of valid ApprovalPolicy records with different trigger thresholds."""
    service = ApprovalPolicyService(db_session)
    p_name = f"High Discount Approval {uuid.uuid4().hex[:6]}"

    policy = await service.create_policy(
        ApprovalPolicyCreate(
            name=p_name,
            discount_above_pct=Decimal("15.00"),
            approval_role=RoleName.SALES_MANAGER,
        )
    )
    assert policy.id is not None
    assert policy.name == p_name
    assert policy.discount_above_pct == Decimal("15.00")
    assert policy.approval_role == RoleName.SALES_MANAGER


@pytest.mark.anyio
async def test_approval_policy_no_trigger_rejected(db_session: AsyncSession):
    """Verify ApprovalPolicy with all trigger thresholds set to None is rejected."""
    service = ApprovalPolicyService(db_session)
    with pytest.raises(CommercialPolicyValidationError) as exc_info:
        await service.create_policy(
            ApprovalPolicyCreate(
                name="Empty Trigger Policy",
                discount_above_pct=None,
                margin_below_pct=None,
                payment_terms_above_days=None,
                approval_role=RoleName.SALES_MANAGER,
            )
        )
    assert "must specify at least one threshold trigger" in str(exc_info.value)


@pytest.mark.anyio
async def test_approval_policy_invalid_role_rejected(db_session: AsyncSession):
    """Verify unsupported operational approver role (e.g. SALES_REP) is rejected."""
    service = ApprovalPolicyService(db_session)
    with pytest.raises(CommercialPolicyValidationError) as exc_info:
        await service.create_policy(
            ApprovalPolicyCreate(
                name="Invalid Role Approval",
                discount_above_pct=Decimal("10.00"),
                approval_role=RoleName.SALES_REP,
            )
        )
    assert "is not allowed. Allowed operational approval roles" in str(exc_info.value)


@pytest.mark.anyio
async def test_approval_policy_multiple_overlapping_triggers_allowed(db_session: AsyncSession):
    """Verify multiple ApprovalPolicies with different triggers can legitimately coexist for same tier."""
    tier_repo = CustomerTierRepository()
    tier = await tier_repo.create_tier(db_session, CustomerTierCreate(name=f"SILVER_{uuid.uuid4().hex[:6]}"))
    await db_session.commit()

    service = ApprovalPolicyService(db_session)

    # Policy 1: High Discount -> Sales Manager
    p1 = await service.create_policy(
        ApprovalPolicyCreate(
            name="Discount > 20% Trigger",
            customer_tier_id=tier.id,
            discount_above_pct=Decimal("20.00"),
            approval_role=RoleName.SALES_MANAGER,
        )
    )

    # Policy 2: Low Margin -> Finance Operations
    p2 = await service.create_policy(
        ApprovalPolicyCreate(
            name="Margin < 10% Trigger",
            customer_tier_id=tier.id,
            margin_below_pct=Decimal("10.00"),
            approval_role=RoleName.FINANCE_OPERATIONS,
        )
    )

    assert p1.id != p2.id
    assert p1.customer_tier_id == tier.id
    assert p2.customer_tier_id == tier.id


@pytest.mark.anyio
async def test_approval_policy_patch_removing_last_trigger_rejected(db_session: AsyncSession):
    """Verify PATCH operation attempting to set last remaining trigger to None is rejected."""
    service = ApprovalPolicyService(db_session)

    policy = await service.create_policy(
        ApprovalPolicyCreate(
            name="Single Trigger Policy",
            payment_terms_above_days=60,
            approval_role=RoleName.FINANCE_OPERATIONS,
        )
    )

    with pytest.raises(CommercialPolicyValidationError) as exc_info:
        await service.update_policy(
            policy.id,
            ApprovalPolicyUpdate(payment_terms_above_days=None),
        )
    assert "must specify at least one threshold trigger" in str(exc_info.value)
