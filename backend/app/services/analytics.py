"""Analytics Service for Phase 6 Part 2."""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.repositories.analytics import AnalyticsRepository
from app.schemas.analytics import GranularityEnum


def parse_date_range(start_date: Optional[datetime], end_date: Optional[datetime]) -> Tuple[datetime, datetime]:
    now_utc = datetime.now(timezone.utc)
    if end_date is None:
        end_date = now_utc
    elif end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    if start_date is None:
        start_date = end_date - timedelta(days=30)
    elif start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)

    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be less than or equal to end_date"
        )
    return start_date, end_date


from typing import Tuple


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AnalyticsRepository(session)

    async def get_overview(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, sales_rep_id: Optional[int] = None
    ) -> Dict[str, Any]:
        s_date, e_date = parse_date_range(start_date, end_date)
        counts = await self.repo.get_overview_counts(s_date, e_date, sales_rep_id)
        currency_totals = await self.repo.get_overview_currency_totals(s_date, e_date, sales_rep_id)
        return {
            "start_date": s_date,
            "end_date": e_date,
            **counts,
            **currency_totals,
        }

    async def get_overview_trend(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, granularity: GranularityEnum = GranularityEnum.DAY, sales_rep_id: Optional[int] = None
    ) -> Dict[str, Any]:
        s_date, e_date = parse_date_range(start_date, end_date)
        # Generate trend point
        trend_item = {
            "period": s_date.strftime("%Y-%m-%d"),
            "quotes_created": (await self.repo.get_overview_counts(s_date, e_date, sales_rep_id))["quotation_count"],
            "quotes_confirmed": (await self.repo.get_overview_counts(s_date, e_date, sales_rep_id))["confirmed_quote_count"],
            "orders_created": (await self.repo.get_overview_counts(s_date, e_date, sales_rep_id))["order_count"],
            "invoices_issued": (await self.repo.get_overview_counts(s_date, e_date, sales_rep_id))["invoice_count"],
            "payments_received_by_currency": (await self.repo.get_overview_currency_totals(s_date, e_date, sales_rep_id))["payments_received"],
            "at_risk_deals": (await self.repo.get_overview_counts(s_date, e_date, sales_rep_id))["at_risk_deal_count"],
        }
        return {
            "start_date": s_date,
            "end_date": e_date,
            "granularity": granularity,
            "trend": [trend_item],
        }

    async def get_quotation_funnel(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, sales_rep_id: Optional[int] = None
    ) -> Dict[str, Any]:
        s_date, e_date = parse_date_range(start_date, end_date)
        res = await self.repo.get_quotation_funnel_data(s_date, e_date, sales_rep_id)
        return {"start_date": s_date, "end_date": e_date, **res}

    async def get_sales_performance(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, sales_rep_id: Optional[int] = None
    ) -> Dict[str, Any]:
        s_date, e_date = parse_date_range(start_date, end_date)
        reps = await self.repo.get_sales_performance_data(s_date, e_date, sales_rep_id)
        return {"start_date": s_date, "end_date": e_date, "reps": reps}

    async def get_discounts(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, sales_rep_id: Optional[int] = None
    ) -> Dict[str, Any]:
        s_date, e_date = parse_date_range(start_date, end_date)
        res = await self.repo.get_discount_analytics(s_date, e_date, sales_rep_id)
        return {"start_date": s_date, "end_date": e_date, **res}

    async def get_margins(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, sales_rep_id: Optional[int] = None
    ) -> Dict[str, Any]:
        s_date, e_date = parse_date_range(start_date, end_date)
        res = await self.repo.get_margin_analytics(s_date, e_date, sales_rep_id)
        return {"start_date": s_date, "end_date": e_date, **res}

    async def get_products(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        s_date, e_date = parse_date_range(start_date, end_date)
        prods = await self.repo.get_product_performance(s_date, e_date, category_id)
        return {"start_date": s_date, "end_date": e_date, "products": prods}

    async def get_product_categories(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        s_date, e_date = parse_date_range(start_date, end_date)
        cats = await self.repo.get_category_performance(s_date, e_date)
        return {"start_date": s_date, "end_date": e_date, "categories": cats}

    async def get_recommendations(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        s_date, e_date = parse_date_range(start_date, end_date)
        return {
            "start_date": s_date,
            "end_date": e_date,
            "recommendation_rule_count": 0,
            "recommendations_added": 0,
            "recommendations_dismissed": 0,
            "acceptance_rate": None,
        }

    async def get_approvals(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, sales_rep_id: Optional[int] = None
    ) -> Dict[str, Any]:
        s_date, e_date = parse_date_range(start_date, end_date)
        res = await self.repo.get_approval_analytics(s_date, e_date, sales_rep_id)
        return {"start_date": s_date, "end_date": e_date, **res}

    async def get_negotiations(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, sales_rep_id: Optional[int] = None
    ) -> Dict[str, Any]:
        s_date, e_date = parse_date_range(start_date, end_date)
        res = await self.repo.get_negotiation_analytics(s_date, e_date, sales_rep_id)
        return {"start_date": s_date, "end_date": e_date, **res}

    async def get_deal_health(self, sales_rep_id: Optional[int] = None) -> Dict[str, Any]:
        return await self.repo.get_deal_health_analytics(sales_rep_id)

    async def get_deal_health_trend(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, granularity: GranularityEnum = GranularityEnum.DAY, sales_rep_id: Optional[int] = None
    ) -> Dict[str, Any]:
        s_date, e_date = parse_date_range(start_date, end_date)
        current = await self.repo.get_deal_health_analytics(sales_rep_id)
        trend_point = {
            "period": s_date.strftime("%Y-%m-%d"),
            "average_score": current["average_health_score"],
            "healthy_count": current["healthy_count"],
            "watch_count": current["watch_count"],
            "at_risk_count": current["at_risk_count"],
            "critical_count": current["critical_count"],
            "alerts_created": current["open_alert_count"],
            "alerts_resolved": 0,
        }
        return {
            "start_date": s_date,
            "end_date": e_date,
            "granularity": granularity,
            "trend": [trend_point],
        }

    async def get_fulfillment(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        s_date, e_date = parse_date_range(start_date, end_date)
        res = await self.repo.get_fulfillment_analytics(s_date, e_date)
        return {"start_date": s_date, "end_date": e_date, **res}

    async def get_warehouses(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        s_date, e_date = parse_date_range(start_date, end_date)
        whs = await self.repo.get_warehouse_analytics(s_date, e_date)
        return {"start_date": s_date, "end_date": e_date, "warehouses": whs}

    async def get_backorders(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        s_date, e_date = parse_date_range(start_date, end_date)
        res = await self.repo.get_backorder_analytics(s_date, e_date)
        return {"start_date": s_date, "end_date": e_date, **res}

    async def get_shipments(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        s_date, e_date = parse_date_range(start_date, end_date)
        res = await self.repo.get_shipment_analytics(s_date, e_date)
        return {"start_date": s_date, "end_date": e_date, **res}

    async def get_billing(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        s_date, e_date = parse_date_range(start_date, end_date)
        res = await self.repo.get_billing_analytics(s_date, e_date)
        return {"start_date": s_date, "end_date": e_date, **res}

    async def get_receivables(self, as_of: Optional[datetime] = None) -> Dict[str, Any]:
        if as_of is None:
            as_of = datetime.now(timezone.utc)
        elif as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=timezone.utc)
        return await self.repo.get_receivables_aging(as_of)

    async def get_payments(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        s_date, e_date = parse_date_range(start_date, end_date)
        res = await self.repo.get_payment_analytics(s_date, e_date)
        return {"start_date": s_date, "end_date": e_date, **res}

    async def get_subscriptions(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        s_date, e_date = parse_date_range(start_date, end_date)
        res = await self.repo.get_subscription_analytics(s_date, e_date)
        return {"start_date": s_date, "end_date": e_date, **res}
