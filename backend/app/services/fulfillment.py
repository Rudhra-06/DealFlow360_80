from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.fulfillment import (
    FulfillmentEngine,
    FulfillmentRecommendation,
    LineRequirement,
    WarehouseInventoryState,
)
from app.models.backorder import Backorder
from app.models.fulfillment_allocation import FulfillmentAllocation
from app.models.fulfillment_plan import FulfillmentPlan
from app.models.inventory import Inventory
from app.models.order_audit_event import OrderAuditEvent
from app.models.sales_order import SalesOrder
from app.models.warehouse import Warehouse
from app.repositories.fulfillment import BackorderRepository, FulfillmentPlanRepository
from app.repositories.sales_order import SalesOrderRepository
from app.services.exceptions import (
    BackorderNotFoundError,
    InsufficientInventoryError,
    InvalidFulfillmentAllocationError,
    InvalidOrderStateError,
    ResourceNotFoundError,
)
from app.services.notification import NotificationService


class FulfillmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.order_repo = SalesOrderRepository()
        self.plan_repo = FulfillmentPlanRepository()
        self.backorder_repo = BackorderRepository()
        self.notif_service = NotificationService(db)

    async def _lock_and_get_inventory(self, product_ids: List[int]) -> Dict[int, List[WarehouseInventoryState]]:
        """Row-locks inventory rows for specified products using FOR UPDATE ordered by warehouse_id, product_id."""
        stmt = (
            select(Inventory, Warehouse)
            .join(Warehouse, Inventory.warehouse_id == Warehouse.id)
            .where(Inventory.product_id.in_(product_ids), Warehouse.is_active == True)
            .order_by(Warehouse.fulfillment_priority.asc(), Warehouse.id.asc(), Inventory.product_id.asc())
            .with_for_update()
        )
        res = await self.db.execute(stmt)
        rows = res.all()

        grid: Dict[int, List[WarehouseInventoryState]] = {}
        for inv, wh in rows:
            avail = inv.on_hand_qty - inv.reserved_qty
            state = WarehouseInventoryState(
                warehouse_id=wh.id,
                warehouse_code=wh.code,
                warehouse_name=wh.name,
                fulfillment_priority=wh.fulfillment_priority,
                shipping_cost_weight=wh.shipping_cost_weight,
                base_shipping_cost=wh.base_shipping_cost,
                available_qty=max(Decimal("0.0000"), avail),
            )
            grid.setdefault(inv.product_id, []).append(state)

        return grid

    async def _get_all_warehouses(self) -> List[WarehouseInventoryState]:
        stmt = select(Warehouse).where(Warehouse.is_active == True).order_by(Warehouse.fulfillment_priority.asc(), Warehouse.id.asc())
        res = await self.db.execute(stmt)
        whs = res.scalars().all()
        return [
            WarehouseInventoryState(
                warehouse_id=w.id,
                warehouse_code=w.code,
                warehouse_name=w.name,
                fulfillment_priority=w.fulfillment_priority,
                shipping_cost_weight=w.shipping_cost_weight,
                base_shipping_cost=w.base_shipping_cost,
                available_qty=Decimal("0.0000"),
            )
            for w in whs
        ]

    async def preview_fulfillment(self, sales_order_id: int) -> FulfillmentRecommendation:
        """Non-persistent preview of system fulfillment recommendation without locking rows or reserving stock."""
        order = await self.order_repo.get_by_id(self.db, sales_order_id)
        if not order:
            raise ResourceNotFoundError(f"SalesOrder with ID {sales_order_id} not found.")

        product_ids = [l.product_id for l in order.lines if l.product_id]
        if not product_ids:
            return FulfillmentRecommendation(
                plan_type="SYSTEM_RECOMMENDED",
                allocations=[],
                backorders=[],
                estimated_shipment_count=0,
                estimated_shipping_cost=Decimal("0.00"),
                explanation="No physical product lines requiring fulfillment.",
            )

        grid = await self._lock_and_get_inventory(product_ids)
        all_whs = await self._get_all_warehouses()

        requirements = [
            LineRequirement(
                sales_order_line_id=l.id,
                product_id=l.product_id,
                product_sku=l.product_sku_snapshot,
                product_name=l.product_name_snapshot,
                required_quantity=l.quantity,
            )
            for l in order.lines
            if l.product_id
        ]

        return FulfillmentEngine.recommend_fulfillment(requirements, grid, all_whs)

    async def generate_and_reserve_initial_fulfillment(
        self, sales_order_id: int, actor_user_id: Optional[int] = None
    ) -> FulfillmentPlan:
        """
        ATOMIC TRANSACTION: Locks inventory rows, evaluates engine, creates active FulfillmentPlan,
        reserves recommended stock in inventory records, and logs backorders for shortage.
        """
        order = await self.order_repo.get_by_id(self.db, sales_order_id)
        if not order:
            raise ResourceNotFoundError(f"SalesOrder with ID {sales_order_id} not found.")

        # Check existing active plan
        existing_plan = await self.plan_repo.get_active_plan_by_order(self.db, sales_order_id)
        if existing_plan:
            return existing_plan

        product_ids = [l.product_id for l in order.lines if l.product_id]
        if not product_ids:
            # Service-only order
            plan = FulfillmentPlan(
                sales_order_id=order.id,
                plan_version=1,
                plan_type="SYSTEM_RECOMMENDED",
                status="ACTIVE",
                estimated_shipment_count=0,
                estimated_shipping_cost=Decimal("0.00"),
                created_by_user_id=actor_user_id,
                confirmed_at=datetime.now(timezone.utc),
            )
            await self.plan_repo.create_plan(self.db, plan)
            return plan

        try:
            # 1. Row lock live inventory
            grid = await self._lock_and_get_inventory(product_ids)
            all_whs = await self._get_all_warehouses()

            requirements = [
                LineRequirement(
                    sales_order_line_id=l.id,
                    product_id=l.product_id,
                    product_sku=l.product_sku_snapshot,
                    product_name=l.product_name_snapshot,
                    required_quantity=l.quantity,
                )
                for l in order.lines
                if l.product_id
            ]

            # 2. Run engine
            rec = FulfillmentEngine.recommend_fulfillment(requirements, grid, all_whs)

            # 3. Build FulfillmentPlan
            plan = FulfillmentPlan(
                sales_order_id=order.id,
                plan_version=1,
                plan_type="SYSTEM_RECOMMENDED",
                status="ACTIVE",
                estimated_shipment_count=rec.estimated_shipment_count,
                estimated_shipping_cost=rec.estimated_shipping_cost,
                created_by_user_id=actor_user_id,
                confirmed_at=datetime.now(timezone.utc),
            )

            # 4. Create allocations & update inventory reserved_qty
            for alloc in rec.allocations:
                plan_alloc = FulfillmentAllocation(
                    sales_order_line_id=alloc.sales_order_line_id,
                    warehouse_id=alloc.warehouse_id,
                    allocated_qty=alloc.allocated_quantity,
                    reserved_qty=alloc.allocated_quantity,
                    fulfilled_qty=Decimal("0.0000"),
                    estimated_shipping_cost=alloc.estimated_shipping_cost,
                )
                plan.allocations.append(plan_alloc)

                # Update live inventory reserved_qty
                inv_stmt = (
                    select(Inventory)
                    .where(
                        Inventory.warehouse_id == alloc.warehouse_id,
                        Inventory.product_id == alloc.product_id,
                    )
                    .with_for_update()
                )
                inv_res = await self.db.execute(inv_stmt)
                inv = inv_res.scalar_one_or_none()
                if inv:
                    inv.reserved_qty += alloc.allocated_quantity

            await self.plan_repo.create_plan(self.db, plan)

            # 5. Record backorders if needed
            has_backorder = False
            for bo in rec.backorders:
                has_backorder = True
                bo_obj = Backorder(
                    sales_order_id=order.id,
                    sales_order_line_id=bo["sales_order_line_id"],
                    requested_qty=bo["requested_quantity"],
                    backordered_qty=bo["backordered_quantity"],
                    status="OPEN",
                )
                await self.backorder_repo.create_backorder(self.db, bo_obj)

            if has_backorder:
                order.status = "BACKORDERED"
            else:
                order.status = "FULFILLMENT"

            # 6. Audit & Notification
            self.db.add(
                OrderAuditEvent(
                    sales_order_id=order.id,
                    actor_user_id=actor_user_id,
                    event_type="INVENTORY_RESERVED",
                    to_status=order.status,
                    event_metadata={
                        "shipment_count": rec.estimated_shipment_count,
                        "has_backorders": has_backorder,
                        "explanation": rec.explanation,
                    },
                )
            )

            await self.db.commit()

            # Post-commit real-time dispatch
            await self.notif_service.dispatch_post_commit_events(
                target_user_ids=[order.sales_rep_id],
                event_name="fulfillment.reserved",
                quotation_id=order.quotation_id,
                payload={"order_id": order.id, "status": order.status},
                title=f"Order {order.order_number} Fulfillment Planned",
                message_text=rec.explanation,
            )

            return await self.plan_repo.get_by_id(self.db, plan.id)
        except Exception:
            await self.db.rollback()
            raise

    async def generate_optimal_fulfillment_plan(
        self, sales_order_id: int, actor_user_id: Optional[int] = None
    ) -> FulfillmentPlan:
        """Canonical public method for generating & reserving system optimal fulfillment plan."""
        return await self.generate_and_reserve_initial_fulfillment(sales_order_id, actor_user_id)

    async def apply_manual_fulfillment_override(
        self,
        sales_order_id: int,
        payload: Dict[str, any] | List[Dict[str, any]],
        actor_user_id: int,
    ) -> FulfillmentPlan:
        """Canonical public method for applying manual fulfillment override plan."""
        if isinstance(payload, dict):
            allocations_input = payload.get("allocations", [])
        else:
            allocations_input = payload

        norm_allocations = []
        for item in allocations_input:
            l_id = item.get("order_line_id") or item.get("sales_order_line_id")
            q_val = item.get("quantity") if item.get("quantity") is not None else item.get("allocated_qty")
            norm_allocations.append({
                "order_line_id": l_id,
                "warehouse_id": item.get("warehouse_id"),
                "quantity": q_val,
            })
        return await self.apply_manual_override(sales_order_id, norm_allocations, actor_user_id)

    async def apply_manual_override(
        self,
        sales_order_id: int,
        allocations_input: List[Dict[str, any]],
        actor_user_id: int,
    ) -> FulfillmentPlan:
        """
        ATOMIC MANUAL OVERRIDE: Releases old unfulfilled reservations, verifies new warehouse requested quantities,
        reserves new inventory, supersedes old plan, and logs audit record.
        """
        order = await self.order_repo.get_by_id(self.db, sales_order_id)
        if not order:
            raise ResourceNotFoundError(f"SalesOrder with ID {sales_order_id} not found.")

        if order.status in {"FULFILLED", "CLOSED", "CANCELLED"}:
            raise InvalidOrderStateError(f"Cannot override fulfillment plan for order in '{order.status}' status.")

        active_plan = await self.plan_repo.get_active_plan_by_order(self.db, sales_order_id)
        line_map = {l.id: l for l in order.lines}

        try:
            # 1. Release previous active plan reservations
            if active_plan:
                for old_alloc in active_plan.allocations:
                    unfulfilled_res = old_alloc.reserved_qty - old_alloc.fulfilled_qty
                    if unfulfilled_res > Decimal("0.0000"):
                        line = line_map.get(old_alloc.sales_order_line_id)
                        if line and line.product_id:
                            inv_stmt = (
                                select(Inventory)
                                .where(
                                    Inventory.warehouse_id == old_alloc.warehouse_id,
                                    Inventory.product_id == line.product_id,
                                )
                                .with_for_update()
                            )
                            inv_res = await self.db.execute(inv_stmt)
                            inv = inv_res.scalar_one_or_none()
                            if inv:
                                inv.reserved_qty = max(Decimal("0.0000"), inv.reserved_qty - unfulfilled_res)

                active_plan.status = "SUPERSEDED"

            # 2. Validate and reserve new manual allocations
            new_version = (active_plan.plan_version + 1) if active_plan else 1
            new_plan = FulfillmentPlan(
                sales_order_id=order.id,
                plan_version=new_version,
                plan_type="MANUAL_OVERRIDE",
                status="ACTIVE",
                created_by_user_id=actor_user_id,
                confirmed_at=datetime.now(timezone.utc),
            )

            wh_ids = {item["warehouse_id"] for item in allocations_input}
            wh_stmt = select(Warehouse).where(Warehouse.id.in_(wh_ids), Warehouse.is_active == True)
            wh_res = await self.db.execute(wh_stmt)
            wh_dict = {w.id: w for w in wh_res.scalars().all()}

            allocated_totals_by_line: Dict[int, Decimal] = {}

            for item in allocations_input:
                line_id = item.get("order_line_id") or item.get("sales_order_line_id")
                wh_id = item["warehouse_id"]
                q_val = item.get("quantity") if item.get("quantity") is not None else item.get("allocated_qty")
                qty = Decimal(str(q_val))

                line = line_map.get(line_id)
                if not line:
                    raise InvalidFulfillmentAllocationError(f"Line ID {line_id} does not belong to order {sales_order_id}.")
                if wh_id not in wh_dict:
                    raise InvalidFulfillmentAllocationError(f"Warehouse ID {wh_id} is inactive or invalid.")

                wh = wh_dict[wh_id]

                # Verify live available stock
                inv_stmt = (
                    select(Inventory)
                    .where(Inventory.warehouse_id == wh_id, Inventory.product_id == line.product_id)
                    .with_for_update()
                )
                inv_res = await self.db.execute(inv_stmt)
                inv = inv_res.scalar_one_or_none()
                avail = (inv.on_hand_qty - inv.reserved_qty) if inv else Decimal("0.0000")

                if qty > avail:
                    raise InsufficientInventoryError(
                        f"Manual override quantity {qty} exceeds available stock {avail} for product {line.product_sku_snapshot} at warehouse {wh.code}."
                    )

                alloc_obj = FulfillmentAllocation(
                    sales_order_line_id=line.id,
                    warehouse_id=wh_id,
                    allocated_qty=qty,
                    reserved_qty=qty,
                    fulfilled_qty=Decimal("0.0000"),
                    estimated_shipping_cost=wh.base_shipping_cost,
                )
                new_plan.allocations.append(alloc_obj)

                if inv:
                    inv.reserved_qty += qty

                allocated_totals_by_line[line.id] = allocated_totals_by_line.get(line.id, Decimal("0.0000")) + qty

            # 3. Update backorders based on manual allocation totals
            open_bos = await self.backorder_repo.list_open_by_order(self.db, sales_order_id)
            for bo in open_bos:
                alloc_total = allocated_totals_by_line.get(bo.sales_order_line_id, Decimal("0.0000"))
                if alloc_total >= bo.requested_qty:
                    bo.status = "RESOLVED"
                    bo.resolved_at = datetime.now(timezone.utc)
                else:
                    bo.backordered_qty = bo.requested_qty - alloc_total

            new_plan.estimated_shipment_count = len(wh_ids)
            new_plan.estimated_shipping_cost = sum((wh_dict[w].base_shipping_cost for w in wh_ids), Decimal("0.00"))

            await self.plan_repo.create_plan(self.db, new_plan)

            # Audit
            self.db.add(
                OrderAuditEvent(
                    sales_order_id=order.id,
                    actor_user_id=actor_user_id,
                    event_type="FULFILLMENT_OVERRIDE",
                    event_metadata={"version": new_version, "shipments": len(wh_ids)},
                )
            )

            await self.db.commit()
            return await self.plan_repo.get_by_id(self.db, new_plan.id)
        except Exception:
            await self.db.rollback()
            raise

    async def consolidate_backorder(self, sales_order_id: int, actor_user_id: int) -> List[Backorder]:
        """Re-evaluates live stock for open backorders and reserves newly available stock."""
        order = await self.order_repo.get_by_id(self.db, sales_order_id)
        if not order:
            raise ResourceNotFoundError(f"SalesOrder with ID {sales_order_id} not found.")

        open_bos = await self.backorder_repo.list_open_by_order(self.db, sales_order_id)
        if not open_bos:
            return []

        active_plan = await self.plan_repo.get_active_plan_by_order(self.db, sales_order_id)
        if not active_plan:
            raise ResourceNotFoundError(f"No active fulfillment plan found for order {sales_order_id}.")

        try:
            for bo in open_bos:
                line = bo.sales_order_line
                if not line or not line.product_id:
                    continue

                rem_needed = bo.backordered_qty
                if rem_needed <= Decimal("0.0000"):
                    continue

                # Query live available stock across active warehouses
                stmt = (
                    select(Inventory, Warehouse)
                    .join(Warehouse, Inventory.warehouse_id == Warehouse.id)
                    .where(Inventory.product_id == line.product_id, Warehouse.is_active == True)
                    .order_by(Warehouse.fulfillment_priority.asc())
                    .with_for_update()
                )
                res = await self.db.execute(stmt)
                rows = res.all()

                for inv, wh in rows:
                    avail = inv.on_hand_qty - inv.reserved_qty
                    if avail > Decimal("0.0000") and rem_needed > Decimal("0.0000"):
                        take_qty = min(rem_needed, avail)

                        # Find or create allocation row
                        alloc = next((a for a in active_plan.allocations if a.sales_order_line_id == line.id and a.warehouse_id == wh.id), None)
                        if alloc:
                            alloc.allocated_qty += take_qty
                            alloc.reserved_qty += take_qty
                        else:
                            alloc = FulfillmentAllocation(
                                sales_order_line_id=line.id,
                                warehouse_id=wh.id,
                                allocated_qty=take_qty,
                                reserved_qty=take_qty,
                                fulfilled_qty=Decimal("0.0000"),
                                estimated_shipping_cost=wh.base_shipping_cost,
                            )
                            active_plan.allocations.append(alloc)

                        inv.reserved_qty += take_qty
                        bo.fulfilled_from_backorder_qty += take_qty
                        bo.backordered_qty -= take_qty
                        rem_needed -= take_qty

                        if bo.backordered_qty <= Decimal("0.0000"):
                            bo.status = "RESOLVED"
                            bo.resolved_at = datetime.now(timezone.utc)
                        else:
                            bo.status = "PARTIALLY_RESOLVED"

            # Check if all backorders resolved
            remaining_bos = await self.backorder_repo.list_open_by_order(self.db, sales_order_id)
            if not remaining_bos:
                order.status = "FULFILLMENT"

            self.db.add(
                OrderAuditEvent(
                    sales_order_id=order.id,
                    actor_user_id=actor_user_id,
                    event_type="BACKORDER_RESOLVED",
                    to_status=order.status,
                )
            )

            await self.db.commit()
            return await self.backorder_repo.list_by_order(self.db, sales_order_id)
        except Exception:
            await self.db.rollback()
            raise
