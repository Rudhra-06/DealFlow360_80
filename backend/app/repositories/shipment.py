from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.sales_order_line import SalesOrderLine
from app.models.shipment import Shipment
from app.models.shipment_line import ShipmentLine
from app.models.warehouse import Warehouse
from app.repositories.base import BaseRepository


class ShipmentRepository(BaseRepository[Shipment]):
    def __init__(self) -> None:
        super().__init__(Shipment)

    def _default_options(self):
        return [
            selectinload(Shipment.warehouse),
            selectinload(Shipment.lines).selectinload(ShipmentLine.sales_order_line).selectinload(SalesOrderLine.product),
            selectinload(Shipment.lines).selectinload(ShipmentLine.fulfillment_allocation),
        ]

    async def create_shipment(self, db: AsyncSession, shipment: Shipment) -> Shipment:
        db.add(shipment)
        await db.flush()
        return shipment

    async def get_by_id(self, db: AsyncSession, shipment_id: int) -> Optional[Shipment]:
        stmt = (
            select(Shipment)
            .options(*self._default_options())
            .execution_options(populate_existing=True)
            .where(Shipment.id == shipment_id)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_number(self, db: AsyncSession, shipment_number: str) -> Optional[Shipment]:
        stmt = select(Shipment).options(*self._default_options()).where(Shipment.shipment_number == shipment_number)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_by_order(self, db: AsyncSession, sales_order_id: int) -> List[Shipment]:
        stmt = (
            select(Shipment)
            .options(*self._default_options())
            .where(Shipment.sales_order_id == sales_order_id)
            .order_by(Shipment.created_at.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
