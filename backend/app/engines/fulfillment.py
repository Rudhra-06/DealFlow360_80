from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional


@dataclass
class LineRequirement:
    sales_order_line_id: int
    product_id: int
    product_sku: str
    product_name: str
    required_quantity: Decimal


@dataclass
class WarehouseInventoryState:
    warehouse_id: int
    warehouse_code: str
    warehouse_name: str
    fulfillment_priority: int
    shipping_cost_weight: Decimal
    base_shipping_cost: Decimal
    available_qty: Decimal


@dataclass
class LineAllocation:
    sales_order_line_id: int
    product_id: int
    warehouse_id: int
    warehouse_code: str
    allocated_quantity: Decimal
    estimated_shipping_cost: Decimal


@dataclass
class FulfillmentRecommendation:
    plan_type: str
    allocations: List[LineAllocation]
    backorders: List[Dict[str, Decimal]]
    estimated_shipment_count: int
    estimated_shipping_cost: Decimal
    explanation: str


class FulfillmentEngine:
    """
    Deterministic side-effect free engine for multi-warehouse stock allocation optimization.
    Objective Hierarchy:
      1. Maximize total quantity fulfilled from live stock.
      2. Minimize number of warehouses / shipments required across all order lines.
      3. Prefer lower configured shipping cost weight / base shipping cost.
      4. Prefer lower fulfillment_priority (e.g. priority 1 before 10).
      5. Deterministic warehouse_id tie-break.
    """

    @staticmethod
    def recommend_fulfillment(
        line_requirements: List[LineRequirement],
        warehouse_inventory: Dict[int, List[WarehouseInventoryState]],  # product_id -> list of warehouse states
        all_warehouses: List[WarehouseInventoryState],
    ) -> FulfillmentRecommendation:
        if not line_requirements:
            return FulfillmentRecommendation(
                plan_type="SYSTEM_RECOMMENDED",
                allocations=[],
                backorders=[],
                estimated_shipment_count=0,
                estimated_shipping_cost=Decimal("0.00"),
                explanation="No order lines provided for fulfillment recommendation.",
            )

        # Build warehouse lookup map
        wh_map = {w.warehouse_id: w for w in all_warehouses}

        # Track remaining required quantities per line
        remaining_req: Dict[int, Decimal] = {l.sales_order_line_id: l.required_quantity for l in line_requirements}
        line_by_id = {l.sales_order_line_id: l for l in line_requirements}

        # Track available stock per (product_id, warehouse_id)
        stock_grid: Dict[int, Dict[int, Decimal]] = {}
        for pid, states in warehouse_inventory.items():
            stock_grid[pid] = {st.warehouse_id: st.available_qty for st in states}

        allocations: List[LineAllocation] = []
        selected_warehouses = set()

        # Step 1: Find best warehouse coverage (warehouses that can fulfill multiple lines)
        # Sort warehouses deterministically by priority, shipping weight, base cost, and ID
        sorted_warehouses = sorted(
            all_warehouses,
            key=lambda w: (
                w.fulfillment_priority,
                w.shipping_cost_weight,
                w.base_shipping_cost,
                w.warehouse_id,
            ),
        )

        # Greedy allocation for each line across sorted warehouses
        for line in line_requirements:
            line_id = line.sales_order_line_id
            pid = line.product_id
            needed = remaining_req[line_id]

            if needed <= Decimal("0.0000"):
                continue

            # Find available stock across sorted warehouses for this product
            wh_avail = stock_grid.get(pid, {})

            # First attempt: Prefer already selected warehouses to minimize total shipment count
            preferred_whs = [w for w in sorted_warehouses if w.warehouse_id in selected_warehouses]
            other_whs = [w for w in sorted_warehouses if w.warehouse_id not in selected_warehouses]
            candidate_whs = preferred_whs + other_whs

            for wh in candidate_whs:
                avail = wh_avail.get(wh.warehouse_id, Decimal("0.0000"))
                if avail > Decimal("0.0000") and needed > Decimal("0.0000"):
                    take_qty = min(needed, avail)

                    allocations.append(
                        LineAllocation(
                            sales_order_line_id=line_id,
                            product_id=pid,
                            warehouse_id=wh.warehouse_id,
                            warehouse_code=wh.warehouse_code,
                            allocated_quantity=take_qty,
                            estimated_shipping_cost=wh.base_shipping_cost,
                        )
                    )

                    stock_grid[pid][wh.warehouse_id] -= take_qty
                    needed -= take_qty
                    remaining_req[line_id] = needed
                    selected_warehouses.add(wh.warehouse_id)

                    if needed <= Decimal("0.0000"):
                        break

        # Step 2: Compute backorders for any unfulfilled line quantities
        backorders: List[Dict[str, Decimal]] = []
        for line in line_requirements:
            rem = remaining_req[line.sales_order_line_id]
            if rem > Decimal("0.0000"):
                backorders.append(
                    {
                        "sales_order_line_id": line.sales_order_line_id,
                        "product_id": line.product_id,
                        "requested_quantity": line.required_quantity,
                        "backordered_quantity": rem,
                    }
                )

        # Step 3: Compute totals & build explanation
        shipment_count = len(selected_warehouses)
        total_shipping_cost = sum(
            (wh_map[w_id].base_shipping_cost for w_id in selected_warehouses), Decimal("0.00")
        )

        if not backorders:
            explanation = (
                f"Full fulfillment achieved across {shipment_count} warehouse shipment(s) "
                f"({', '.join(wh_map[w].warehouse_code for w in selected_warehouses)})."
            )
        else:
            fulfilled_lines_cnt = len(line_requirements) - len(backorders)
            explanation = (
                f"Partial fulfillment achieved across {shipment_count} warehouse shipment(s). "
                f"{len(backorders)} item line(s) backordered due to stock limits."
            )

        return FulfillmentRecommendation(
            plan_type="SYSTEM_RECOMMENDED",
            allocations=allocations,
            backorders=backorders,
            estimated_shipment_count=shipment_count,
            estimated_shipping_cost=total_shipping_cost,
            explanation=explanation,
        )
