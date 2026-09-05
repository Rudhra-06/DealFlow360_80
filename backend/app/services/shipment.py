from datetime import datetime, timezone
import secrets
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import Inventory
from app.models.order_audit_event import OrderAuditEvent
from app.models.sales_order import SalesOrder
from app.models.shipment import Shipment
from app.models.shipment_line import ShipmentLine
from app.repositories.fulfillment import FulfillmentPlanRepository
from app.repositories.sales_order import SalesOrderRepository
from app.repositories.shipment import ShipmentRepository
from app.services.exceptions import (
    InvalidOrderStateError,
    ResourceNotFoundError,
    ShipmentStateError,
)
from app.services.notification import NotificationService


class ShipmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.order_repo = SalesOrderRepository()
        self.plan_repo = FulfillmentPlanRepository()
        self.shipment_repo = ShipmentRepository()
        self.notif_service = NotificationService(db)

    def _generate_shipment_number(self) -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        rand_suffix = secrets.token_hex(4).upper()
        return f"SHP-{date_str}-{rand_suffix}"

    async def generate_shipments_from_plan(
        self, sales_order_id: int, actor_user_id: Optional[int] = None
    ) -> List[Shipment]:
        """Idempotently generates physical shipment headers and lines grouped by warehouse from active allocations."""
        order = await self.order_repo.get_by_id(self.db, sales_order_id)
        if not order:
            raise ResourceNotFoundError(f"SalesOrder with ID {sales_order_id} not found.")

        plan = await self.plan_repo.get_active_plan_by_order(self.db, sales_order_id)
        if not plan:
            raise ResourceNotFoundError(f"No active fulfillment plan found for order {sales_order_id}.")

        existing_shipments = await self.shipment_repo.list_by_order(self.db, sales_order_id)
        if existing_shipments:
            return existing_shipments

        # Group allocations by warehouse
        allocs_by_wh: dict = {}
        for alloc in plan.allocations:
            unshipped_qty = alloc.reserved_qty - alloc.fulfilled_qty
            if unshipped_qty > 0:
                allocs_by_wh.setdefault(alloc.warehouse_id, []).append((alloc, unshipped_qty))

        if not allocs_by_wh:
            return []

        try:
            created_shipments = []
            for wh_id, items in allocs_by_wh.items():
                est_cost = sum((item[0].estimated_shipping_cost for item in items), 0)
                shp = Shipment(
                    shipment_number=self._generate_shipment_number(),
                    sales_order_id=order.id,
                    warehouse_id=wh_id,
                    status="PLANNED",
                    estimated_cost=est_cost,
                )

                for alloc, unshipped_qty in items:
                    line_obj = ShipmentLine(
                        sales_order_line_id=alloc.sales_order_line_id,
                        fulfillment_allocation_id=alloc.id,
                        quantity=unshipped_qty,
                    )
                    shp.lines.append(line_obj)

                await self.shipment_repo.create_shipment(self.db, shp)
                created_shipments.append(shp)

            self.db.add(
                OrderAuditEvent(
                    sales_order_id=order.id,
                    actor_user_id=actor_user_id,
                    event_type="SHIPMENT_CREATED",
                    event_metadata={"shipment_count": len(created_shipments)},
                )
            )

            await self.db.commit()
            return await self.shipment_repo.list_by_order(self.db, sales_order_id)
        except Exception:
            await self.db.rollback()
            raise

    async def mark_shipment_shipped(self, shipment_id: int, actor_user_id: Optional[int] = None) -> Shipment:
        """
        ATOMIC STOCK CONSUMPTION:
        Decrements physical stock on_hand_qty and reserved_qty in PostgreSQL inventory records.
        """
        shp = await self.shipment_repo.get_by_id(self.db, shipment_id)
        if not shp:
            raise ResourceNotFoundError(f"Shipment with ID {shipment_id} not found.")

        if shp.status not in {"PLANNED", "READY"}:
            raise ShipmentStateError(f"Cannot ship shipment {shipment_id} in '{shp.status}' status.")

        order = await self.order_repo.get_by_id(self.db, shp.sales_order_id)

        try:
            # Consume stock for each shipment line
            for s_line in shp.lines:
                alloc = s_line.fulfillment_allocation
                so_line = s_line.sales_order_line

                if so_line and so_line.product_id:
                    inv_stmt = (
                        select(Inventory)
                        .where(
                            Inventory.warehouse_id == shp.warehouse_id,
                            Inventory.product_id == so_line.product_id,
                        )
                        .with_for_update()
                    )
                    inv_res = await self.db.execute(inv_stmt)
                    inv = inv_res.scalar_one_or_none()

                    if inv:
                        inv.on_hand_qty = max(0, inv.on_hand_qty - s_line.quantity)
                        inv.reserved_qty = max(0, inv.reserved_qty - s_line.quantity)

                if alloc:
                    alloc.fulfilled_qty += s_line.quantity

            now = datetime.now(timezone.utc)
            shp.status = "SHIPPED"
            shp.shipped_at = now

            # Check all shipments status for order
            all_shps = await self.shipment_repo.list_by_order(self.db, order.id)
            all_shipped = all((s.id == shp.id or s.status in {"SHIPPED", "DELIVERED"}) for s in all_shps)

            if all_shipped:
                order.status = "FULFILLED"
            else:
                order.status = "PARTIALLY_FULFILLED"

            self.db.add(
                OrderAuditEvent(
                    sales_order_id=order.id,
                    actor_user_id=actor_user_id,
                    event_type="SHIPMENT_SHIPPED",
                    to_status=order.status,
                    event_metadata={"shipment_number": shp.shipment_number},
                )
            )

            await self.db.commit()

            # Post-commit notification
            await self.notif_service.dispatch_post_commit_events(
                target_user_ids=[order.sales_rep_id],
                event_name="shipment.shipped",
                quotation_id=order.quotation_id,
                payload={"shipment_number": shp.shipment_number, "status": shp.status},
                title=f"Shipment {shp.shipment_number} Dispatched",
                message_text=f"Shipment {shp.shipment_number} has been dispatched from warehouse.",
            )

            return await self.shipment_repo.get_by_id(self.db, shp.id)
        except Exception:
            await self.db.rollback()
            raise

    async def mark_shipment_delivered(self, shipment_id: int, actor_user_id: Optional[int] = None) -> Shipment:
        """Sets shipment status to DELIVERED without re-decrementing inventory."""
        shp = await self.shipment_repo.get_by_id(self.db, shipment_id)
        if not shp:
            raise ResourceNotFoundError(f"Shipment with ID {shipment_id} not found.")

        if shp.status != "SHIPPED":
            raise ShipmentStateError(f"Cannot mark shipment delivered while in '{shp.status}' status (must be SHIPPED).")

        try:
            shp.status = "DELIVERED"
            shp.delivered_at = datetime.now(timezone.utc)

            self.db.add(
                OrderAuditEvent(
                    sales_order_id=shp.sales_order_id,
                    actor_user_id=actor_user_id,
                    event_type="SHIPMENT_DELIVERED",
                    event_metadata={"shipment_number": shp.shipment_number},
                )
            )

            await self.db.commit()
            return await self.shipment_repo.get_by_id(self.db, shp.id)
        except Exception:
            await self.db.rollback()
            raise

    async def create_and_process_shipment(
        self,
        shipment_payload: dict,
        actor_user_id: int,
    ) -> Shipment:
        """
        Canonical orchestration method:
        1. Validates order and active fulfillment plan.
        2. Creates shipment header and line items.
        3. Executes mark_shipment_shipped to row-lock inventory, decrement stock/reserved quantities, update allocations, and update order status.
        """
        sales_order_id = shipment_payload["sales_order_id"]
        warehouse_id = shipment_payload["warehouse_id"]
        carrier = shipment_payload.get("carrier")
        tracking_number = shipment_payload.get("tracking_number")
        lines_input = shipment_payload.get("lines", [])

        order = await self.order_repo.get_by_id(self.db, sales_order_id)
        if not order:
            raise ResourceNotFoundError(f"SalesOrder with ID {sales_order_id} not found.")

        plan = await self.plan_repo.get_active_plan_by_order(self.db, sales_order_id)
        if not plan:
            raise ResourceNotFoundError(f"No active fulfillment plan found for order {sales_order_id}.")

        try:
            shp = Shipment(
                shipment_number=self._generate_shipment_number(),
                sales_order_id=order.id,
                warehouse_id=warehouse_id,
                status="PLANNED",
                estimated_cost=Decimal("0.00"),
            )

            for line_item in lines_input:
                so_line_id = line_item["sales_order_line_id"]
                shipped_qty = Decimal(str(line_item.get("shipped_qty") or line_item.get("quantity") or 0))

                alloc = next(
                    (a for a in plan.allocations if a.sales_order_line_id == so_line_id and a.warehouse_id == warehouse_id),
                    None
                )
                if not alloc:
                    alloc = next((a for a in plan.allocations if a.sales_order_line_id == so_line_id), None)
                if not alloc:
                    raise ResourceNotFoundError(f"No fulfillment allocation found for order line {so_line_id}.")

                shp_line = ShipmentLine(
                    sales_order_line_id=so_line_id,
                    fulfillment_allocation_id=alloc.id,
                    quantity=shipped_qty,
                )
                shp.lines.append(shp_line)

            await self.shipment_repo.create_shipment(self.db, shp)
            await self.db.flush()

            return await self.mark_shipment_shipped(shp.id, actor_user_id)
        except Exception:
            await self.db.rollback()
            raise

