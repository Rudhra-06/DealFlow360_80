from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.models.deal_alert import DealAlert
from app.models.quotation import Quotation
from app.repositories.base import BaseRepository


class DealAlertRepository(BaseRepository[DealAlert]):
    def __init__(self) -> None:
        super().__init__(DealAlert)

    def _default_options(self):
        return [
            selectinload(DealAlert.quotation),
            selectinload(DealAlert.sales_order),
            selectinload(DealAlert.snapshot),
            selectinload(DealAlert.assigned_user),
            selectinload(DealAlert.acknowledged_by_user),
            selectinload(DealAlert.resolved_by_user),
            selectinload(DealAlert.actions),
        ]

    async def create_alert(self, db: AsyncSession, alert: DealAlert) -> DealAlert:
        db.add(alert)
        await db.flush()
        return alert

    async def get_by_id(self, db: AsyncSession, alert_id: int) -> Optional[DealAlert]:
        stmt = select(DealAlert).options(*self._default_options()).where(DealAlert.id == alert_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_active_alert_by_type(
        self, db: AsyncSession, quotation_id: int, alert_type: str
    ) -> Optional[DealAlert]:
        """Finds an existing OPEN or ACKNOWLEDGED alert for the same quotation and alert type."""
        stmt = (
            select(DealAlert)
            .options(*self._default_options())
            .where(
                DealAlert.quotation_id == quotation_id,
                DealAlert.alert_type == alert_type,
                DealAlert.status.in_(["OPEN", "ACKNOWLEDGED"]),
            )
            .order_by(DealAlert.created_at.desc())
        )
        res = await db.execute(stmt)
        return res.scalars().first()

    async def list_alerts(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        alert_type: Optional[str] = None,
        quotation_id: Optional[int] = None,
        assigned_user_id: Optional[int] = None,
        sales_rep_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[DealAlert]:
        stmt = select(DealAlert).options(*self._default_options()).join(Quotation, DealAlert.quotation_id == Quotation.id)

        if status:
            stmt = stmt.where(DealAlert.status == status)
        if severity:
            stmt = stmt.where(DealAlert.severity == severity)
        if alert_type:
            stmt = stmt.where(DealAlert.alert_type == alert_type)
        if quotation_id:
            stmt = stmt.where(DealAlert.quotation_id == quotation_id)
        if assigned_user_id:
            stmt = stmt.where(DealAlert.assigned_user_id == assigned_user_id)
        if sales_rep_id:
            stmt = stmt.where(Quotation.sales_rep_id == sales_rep_id)
        if customer_id:
            stmt = stmt.where(Quotation.customer_id == customer_id)

        stmt = stmt.order_by(DealAlert.created_at.desc(), DealAlert.id.desc()).offset(offset).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())
