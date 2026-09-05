import sys
import uuid
from pathlib import Path
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.schemas.billing_plan import BillingPlanCreate, BillingPlanUpdate
from app.services.billing_plan import BillingPlanService
from app.services.exceptions import CommercialPolicyValidationError, DuplicateResourceError


@pytest.mark.anyio
async def test_billing_plan_one_time_creation_success(db_session: AsyncSession):
    """Verify ONE_TIME billing plan creation with billing_interval_months=None."""
    service = BillingPlanService(db_session)
    code = f"ONE_TIME_{uuid.uuid4().hex[:6]}"

    plan = await service.create_plan(
        BillingPlanCreate(
            code=code,
            name="One-Time Standard Billing",
            billing_type="ONE_TIME",
            billing_interval_months=None,
            payment_due_days=30,
        )
    )
    assert plan.id is not None
    assert plan.code == code.upper()
    assert plan.billing_type == "ONE_TIME"
    assert plan.billing_interval_months is None


@pytest.mark.anyio
async def test_billing_plan_recurring_creation_success(db_session: AsyncSession):
    """Verify RECURRING billing plan creation with valid interval (e.g. 1 month, 3 months, 12 months)."""
    service = BillingPlanService(db_session)

    p1 = await service.create_plan(
        BillingPlanCreate(
            code=f"MONTHLY_{uuid.uuid4().hex[:6]}",
            name="Monthly Subscription",
            billing_type="RECURRING",
            billing_interval_months=1,
            payment_due_days=15,
        )
    )
    assert p1.billing_type == "RECURRING"
    assert p1.billing_interval_months == 1

    p2 = await service.create_plan(
        BillingPlanCreate(
            code=f"ANNUAL_{uuid.uuid4().hex[:6]}",
            name="Annual Subscription",
            billing_type="RECURRING",
            billing_interval_months=12,
            payment_due_days=30,
        )
    )
    assert p2.billing_type == "RECURRING"
    assert p2.billing_interval_months == 12


@pytest.mark.anyio
async def test_billing_plan_invalid_one_time_with_interval_rejected(db_session: AsyncSession):
    """Verify ONE_TIME billing plan with non-null billing_interval_months is rejected."""
    service = BillingPlanService(db_session)
    with pytest.raises(CommercialPolicyValidationError) as exc_info:
        await service.create_plan(
            BillingPlanCreate(
                code=f"BAD_ONETIME_{uuid.uuid4().hex[:6]}",
                name="Bad One Time",
                billing_type="ONE_TIME",
                billing_interval_months=1,
            )
        )
    assert "billing_interval_months must be null for ONE_TIME" in str(exc_info.value)


@pytest.mark.anyio
async def test_billing_plan_invalid_recurring_without_interval_rejected(db_session: AsyncSession):
    """Verify RECURRING billing plan with null interval is rejected."""
    service = BillingPlanService(db_session)
    with pytest.raises(CommercialPolicyValidationError) as exc_info:
        await service.create_plan(
            BillingPlanCreate(
                code=f"BAD_RECURRING_{uuid.uuid4().hex[:6]}",
                name="Bad Recurring",
                billing_type="RECURRING",
                billing_interval_months=None,
            )
        )
    assert "billing_interval_months must be an integer >= 1" in str(exc_info.value)


@pytest.mark.anyio
async def test_billing_plan_duplicate_code_rejected(db_session: AsyncSession):
    """Verify duplicate billing plan code (ignoring case and whitespace) is rejected with DuplicateResourceError."""
    service = BillingPlanService(db_session)
    uid = uuid.uuid4().hex[:6]
    code = f"DUP_PLAN_{uid}"

    await service.create_plan(
        BillingPlanCreate(
            code=code,
            name="Original Plan",
            billing_type="ONE_TIME",
        )
    )

    with pytest.raises(DuplicateResourceError) as exc_info:
        await service.create_plan(
            BillingPlanCreate(
                code=f"  dup_plan_{uid}  ",
                name="Duplicate Code Plan",
                billing_type="ONE_TIME",
            )
        )
    assert "already exists" in str(exc_info.value)
