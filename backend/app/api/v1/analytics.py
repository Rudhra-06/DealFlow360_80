"""Analytics API Router for Phase 6 Part 2."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.role import RoleName
from app.models.user import User
from app.api.dependencies.auth import get_current_active_user, require_roles
from app.schemas.analytics import (
    ExecutiveOverviewResponse,
    ExecutiveOverviewTrendResponse,
    QuotationFunnelResponse,
    SalesPerformanceResponse,
    DiscountAnalyticsResponse,
    MarginAnalyticsResponse,
    Customer360Response,
    ProductPerformanceResponse,
    ProductCategoryPerformanceResponse,
    RecommendationAnalyticsResponse,
    ApprovalAnalyticsResponse,
    NegotiationAnalyticsResponse,
    DealHealthAnalyticsResponse,
    DealHealthTrendResponse,
    FulfillmentAnalyticsResponse,
    WarehouseAnalyticsResponse,
    BackorderAnalyticsResponse,
    ShipmentAnalyticsResponse,
    BillingAnalyticsResponse,
    ReceivablesAnalyticsResponse,
    PaymentAnalyticsResponse,
    SubscriptionAnalyticsResponse,
    GranularityEnum,
)
from app.services.analytics import AnalyticsService
from app.services.customer_360 import Customer360Service

router = APIRouter(prefix="/analytics", tags=["Analytics"])

INTERNAL_ROLES = [
    RoleName.ADMIN,
    RoleName.SALES_MANAGER,
    RoleName.SALES_REP,
    RoleName.FINANCE_OPERATIONS,
]


@router.get(
    "/overview",
    response_model=ExecutiveOverviewResponse,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_overview(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    sales_rep_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = AnalyticsService(db)
    # Scope for sales rep if not admin/manager
    role_names = [r.name for r in current_user.roles] if hasattr(current_user, "roles") else []
    if "SALES_REP" in role_names and "ADMIN" not in role_names and "SALES_MANAGER" not in role_names:
        sales_rep_id = current_user.id
    return await service.get_overview(start_date, end_date, sales_rep_id)


@router.get(
    "/overview/trend",
    response_model=ExecutiveOverviewTrendResponse,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_overview_trend(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    granularity: GranularityEnum = Query(GranularityEnum.DAY),
    sales_rep_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = AnalyticsService(db)
    role_names = [r.name for r in current_user.roles] if hasattr(current_user, "roles") else []
    if "SALES_REP" in role_names and "ADMIN" not in role_names and "SALES_MANAGER" not in role_names:
        sales_rep_id = current_user.id
    return await service.get_overview_trend(start_date, end_date, granularity, sales_rep_id)


@router.get(
    "/quotation-funnel",
    response_model=QuotationFunnelResponse,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_quotation_funnel(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    sales_rep_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = AnalyticsService(db)
    role_names = [r.name for r in current_user.roles] if hasattr(current_user, "roles") else []
    if "SALES_REP" in role_names and "ADMIN" not in role_names and "SALES_MANAGER" not in role_names:
        sales_rep_id = current_user.id
    return await service.get_quotation_funnel(start_date, end_date, sales_rep_id)


@router.get(
    "/sales-performance",
    response_model=SalesPerformanceResponse,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_sales_performance(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    sales_rep_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = AnalyticsService(db)
    role_names = [r.name for r in current_user.roles] if hasattr(current_user, "roles") else []
    if "SALES_REP" in role_names and "ADMIN" not in role_names and "SALES_MANAGER" not in role_names:
        sales_rep_id = current_user.id
    return await service.get_sales_performance(start_date, end_date, sales_rep_id)


@router.get(
    "/discounts",
    response_model=DiscountAnalyticsResponse,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_discounts(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    sales_rep_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = AnalyticsService(db)
    role_names = [r.name for r in current_user.roles] if hasattr(current_user, "roles") else []
    if "SALES_REP" in role_names and "ADMIN" not in role_names and "SALES_MANAGER" not in role_names:
        sales_rep_id = current_user.id
    return await service.get_discounts(start_date, end_date, sales_rep_id)


@router.get(
    "/margins",
    response_model=MarginAnalyticsResponse,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_margins(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    sales_rep_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = AnalyticsService(db)
    role_names = [r.name for r in current_user.roles] if hasattr(current_user, "roles") else []
    if "SALES_REP" in role_names and "ADMIN" not in role_names and "SALES_MANAGER" not in role_names:
        sales_rep_id = current_user.id
    return await service.get_margins(start_date, end_date, sales_rep_id)


@router.get(
    "/customers/{customer_id}/360",
    response_model=Customer360Response,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_customer_360(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = Customer360Service(db)
    return await service.get_customer_360(customer_id, current_user)


@router.get(
    "/products",
    response_model=ProductPerformanceResponse,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_products(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    category_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_products(start_date, end_date, category_id)


@router.get(
    "/product-categories",
    response_model=ProductCategoryPerformanceResponse,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_product_categories(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_product_categories(start_date, end_date)


@router.get(
    "/recommendations",
    response_model=RecommendationAnalyticsResponse,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_recommendations(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_recommendations(start_date, end_date)


@router.get(
    "/approvals",
    response_model=ApprovalAnalyticsResponse,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_approvals(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    sales_rep_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = AnalyticsService(db)
    role_names = [r.name for r in current_user.roles] if hasattr(current_user, "roles") else []
    if "SALES_REP" in role_names and "ADMIN" not in role_names and "SALES_MANAGER" not in role_names:
        sales_rep_id = current_user.id
    return await service.get_approvals(start_date, end_date, sales_rep_id)


@router.get(
    "/negotiations",
    response_model=NegotiationAnalyticsResponse,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_negotiations(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    sales_rep_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = AnalyticsService(db)
    role_names = [r.name for r in current_user.roles] if hasattr(current_user, "roles") else []
    if "SALES_REP" in role_names and "ADMIN" not in role_names and "SALES_MANAGER" not in role_names:
        sales_rep_id = current_user.id
    return await service.get_negotiations(start_date, end_date, sales_rep_id)


@router.get(
    "/deal-health",
    response_model=DealHealthAnalyticsResponse,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_deal_health(
    sales_rep_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = AnalyticsService(db)
    role_names = [r.name for r in current_user.roles] if hasattr(current_user, "roles") else []
    if "SALES_REP" in role_names and "ADMIN" not in role_names and "SALES_MANAGER" not in role_names:
        sales_rep_id = current_user.id
    return await service.get_deal_health(sales_rep_id)


@router.get(
    "/deal-health/trend",
    response_model=DealHealthTrendResponse,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_deal_health_trend(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    granularity: GranularityEnum = Query(GranularityEnum.DAY),
    sales_rep_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = AnalyticsService(db)
    role_names = [r.name for r in current_user.roles] if hasattr(current_user, "roles") else []
    if "SALES_REP" in role_names and "ADMIN" not in role_names and "SALES_MANAGER" not in role_names:
        sales_rep_id = current_user.id
    return await service.get_deal_health_trend(start_date, end_date, granularity, sales_rep_id)


@router.get(
    "/fulfillment",
    response_model=FulfillmentAnalyticsResponse,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_fulfillment(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_fulfillment(start_date, end_date)


@router.get(
    "/warehouses",
    response_model=WarehouseAnalyticsResponse,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_warehouses(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_warehouses(start_date, end_date)


@router.get(
    "/backorders",
    response_model=BackorderAnalyticsResponse,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_backorders(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_backorders(start_date, end_date)


@router.get(
    "/shipments",
    response_model=ShipmentAnalyticsResponse,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_shipments(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_shipments(start_date, end_date)


@router.get(
    "/billing",
    response_model=BillingAnalyticsResponse,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_billing(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_billing(start_date, end_date)


@router.get(
    "/receivables",
    response_model=ReceivablesAnalyticsResponse,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_receivables(
    as_of: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_receivables(as_of)


@router.get(
    "/payments",
    response_model=PaymentAnalyticsResponse,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_payments(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_payments(start_date, end_date)


@router.get(
    "/subscriptions",
    response_model=SubscriptionAnalyticsResponse,
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_subscriptions(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_subscriptions(start_date, end_date)


@router.get(
    "/executive-summary-text",
    dependencies=[Depends(require_roles(*INTERNAL_ROLES))],
)
async def get_executive_summary_text(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    sales_rep_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = AnalyticsService(db)
    role_names = [r.name for r in current_user.roles] if hasattr(current_user, "roles") else []
    if "SALES_REP" in role_names and "ADMIN" not in role_names and "SALES_MANAGER" not in role_names:
        sales_rep_id = current_user.id

    data = await service.get_overview(start_date, end_date, sales_rep_id)

    q_cnt = data.get("quotation_count", 0)
    c_cnt = data.get("confirmed_quote_count", 0)
    rate = data.get("confirmation_rate")
    rate_str = f"{rate}%" if rate is not None else "N/A"
    risk_cnt = data.get("at_risk_deal_count", 0)
    crit_cnt = data.get("critical_deal_count", 0)

    rev_by_curr = data.get("confirmed_order_value", {})
    rev_str = ", ".join(f"{curr} {val}" for curr, val in rev_by_curr.items()) if rev_by_curr else "None"

    rec_by_curr = data.get("outstanding_receivables", {})
    rec_str = ", ".join(f"{curr} {val}" for curr, val in rec_by_curr.items()) if rec_by_curr else "None"

    narrative = (
        f"{q_cnt} quotations were created in the selected period, with {c_cnt} confirmed (confirmation rate of {rate_str}). "
        f"Total confirmed order value: {rev_str}. "
        f"There are currently {risk_cnt} open deals at risk and {crit_cnt} critical deals requiring management attention. "
        f"Outstanding receivables balance: {rec_str}."
    )

    return {
        "start_date": data["start_date"],
        "end_date": data["end_date"],
        "narrative": narrative,
    }

