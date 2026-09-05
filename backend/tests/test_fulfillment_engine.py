from decimal import Decimal
from app.engines.fulfillment import (
    FulfillmentEngine,
    LineRequirement,
    WarehouseInventoryState,
)


def test_fulfillment_engine_single_warehouse():
    engine = FulfillmentEngine()
    reqs = [
        LineRequirement(
            sales_order_line_id=1,
            product_id=101,
            product_sku="SKU-101",
            product_name="Product 101",
            required_quantity=Decimal("10"),
        )
    ]
    wh = WarehouseInventoryState(
        warehouse_id=1,
        warehouse_code="WH-MAIN",
        warehouse_name="Main Warehouse",
        fulfillment_priority=1,
        shipping_cost_weight=Decimal("1.0"),
        base_shipping_cost=Decimal("10.00"),
        available_qty=Decimal("15"),
    )

    inventory_grid = {101: [wh]}
    rec = engine.recommend_fulfillment(reqs, inventory_grid, [wh])

    assert len(rec.allocations) == 1
    assert rec.allocations[0].sales_order_line_id == 1
    assert rec.allocations[0].warehouse_id == 1
    assert rec.allocations[0].allocated_quantity == Decimal("10")
    assert len(rec.backorders) == 0


def test_fulfillment_engine_multi_warehouse_split():
    engine = FulfillmentEngine()
    reqs = [
        LineRequirement(
            sales_order_line_id=1,
            product_id=101,
            product_sku="SKU-101",
            product_name="Product 101",
            required_quantity=Decimal("20"),
        )
    ]
    wh1 = WarehouseInventoryState(
        warehouse_id=1,
        warehouse_code="WH-A",
        warehouse_name="Warehouse A",
        fulfillment_priority=1,
        shipping_cost_weight=Decimal("1.0"),
        base_shipping_cost=Decimal("10.00"),
        available_qty=Decimal("12"),
    )
    wh2 = WarehouseInventoryState(
        warehouse_id=2,
        warehouse_code="WH-B",
        warehouse_name="Warehouse B",
        fulfillment_priority=2,
        shipping_cost_weight=Decimal("1.5"),
        base_shipping_cost=Decimal("15.00"),
        available_qty=Decimal("15"),
    )

    inventory_grid = {101: [wh1, wh2]}
    rec = engine.recommend_fulfillment(reqs, inventory_grid, [wh1, wh2])

    assert len(rec.allocations) == 2
    alloc_wh1 = next(a for a in rec.allocations if a.warehouse_id == 1)
    alloc_wh2 = next(a for a in rec.allocations if a.warehouse_id == 2)
    assert alloc_wh1.allocated_quantity == Decimal("12")
    assert alloc_wh2.allocated_quantity == Decimal("8")
    assert len(rec.backorders) == 0


def test_fulfillment_engine_backorder_generation():
    engine = FulfillmentEngine()
    reqs = [
        LineRequirement(
            sales_order_line_id=1,
            product_id=101,
            product_sku="SKU-101",
            product_name="Product 101",
            required_quantity=Decimal("25"),
        )
    ]
    wh = WarehouseInventoryState(
        warehouse_id=1,
        warehouse_code="WH-LIMITED",
        warehouse_name="Limited Stock Warehouse",
        fulfillment_priority=1,
        shipping_cost_weight=Decimal("1.0"),
        base_shipping_cost=Decimal("10.00"),
        available_qty=Decimal("10"),
    )

    inventory_grid = {101: [wh]}
    rec = engine.recommend_fulfillment(reqs, inventory_grid, [wh])

    assert len(rec.allocations) == 1
    assert rec.allocations[0].allocated_quantity == Decimal("10")
    assert len(rec.backorders) == 1
    assert rec.backorders[0]["backordered_quantity"] == Decimal("15")
