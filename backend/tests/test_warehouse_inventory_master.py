import uuid
from decimal import Decimal
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.inventory import InventoryCreate, InventoryUpdate
from app.schemas.product import ProductCreate
from app.schemas.product_category import ProductCategoryCreate
from app.schemas.warehouse import WarehouseCreate
from app.services.exceptions import (
    DuplicateResourceError,
    InactiveReferenceError,
    InvalidReferenceError,
    InventoryValidationError,
    ResourceNotFoundError,
)
from app.services.inventory import InventoryService
from app.services.product import ProductService
from app.services.product_category import ProductCategoryService
from app.services.warehouse import WarehouseService


@pytest.mark.anyio
async def test_warehouse_and_inventory_service_crud(db_session: AsyncSession):
    wh_service = WarehouseService(db_session)
    wh = await wh_service.create_warehouse(
        WarehouseCreate(
            code=f"  wh-{uuid.uuid4().hex[:6]}  ",
            name="Main Chicago Hub",
            location="Chicago",
        )
    )
    assert wh.id is not None
    assert wh.code.startswith("WH-")

    cat_service = ProductCategoryService(db_session)
    cat = await cat_service.create_category(
        ProductCategoryCreate(name=f"CAT_WH_{uuid.uuid4().hex[:6]}")
    )

    prod_service = ProductService(db_session)
    prod = await prod_service.create_product(
        ProductCreate(
            sku=f"SKU-WH-{uuid.uuid4().hex[:6]}",
            name="Storage Unit",
            category_id=cat.id,
        )
    )

    inv_service = InventoryService(db_session)

    # Create Inventory
    inv = await inv_service.create_inventory(
        InventoryCreate(
            warehouse_id=wh.id,
            product_id=prod.id,
            on_hand_qty=Decimal("150.000"),
            reorder_level=Decimal("20.000"),
        )
    )
    assert inv.id is not None
    assert inv.on_hand_qty == Decimal("150.000")
    assert inv.reserved_qty == Decimal("0.000")

    # Duplicate warehouse + product mapping raises error
    with pytest.raises(DuplicateResourceError):
        await inv_service.create_inventory(
            InventoryCreate(
                warehouse_id=wh.id,
                product_id=prod.id,
                on_hand_qty=Decimal("50.000"),
            )
        )

    # Update inventory on_hand_qty
    updated = await inv_service.update_inventory(
        inv.id, InventoryUpdate(on_hand_qty=Decimal("200.000"))
    )
    assert updated.on_hand_qty == Decimal("200.000")


@pytest.mark.anyio
async def test_inventory_below_reserved_qty_validation(db_session: AsyncSession):
    wh_service = WarehouseService(db_session)
    wh = await wh_service.create_warehouse(
        WarehouseCreate(code=f"WH-RES-{uuid.uuid4().hex[:6]}", name="Reserved Test Hub")
    )

    cat_service = ProductCategoryService(db_session)
    cat = await cat_service.create_category(
        ProductCategoryCreate(name=f"CAT_RES_{uuid.uuid4().hex[:6]}")
    )

    prod_service = ProductService(db_session)
    prod = await prod_service.create_product(
        ProductCreate(
            sku=f"SKU-RES-{uuid.uuid4().hex[:6]}",
            name="Reserved Test Item",
            category_id=cat.id,
        )
    )

    inv_service = InventoryService(db_session)
    inv = await inv_service.create_inventory(
        InventoryCreate(
            warehouse_id=wh.id,
            product_id=prod.id,
            on_hand_qty=Decimal("100.000"),
        )
    )

    # Simulate internal reservation
    inv.reserved_qty = Decimal("40.000")
    await db_session.commit()

    # Attempting to set on_hand_qty below reserved_qty (e.g. 20 < 40) fails
    with pytest.raises(InventoryValidationError):
        await inv_service.update_inventory(
            inv.id, InventoryUpdate(on_hand_qty=Decimal("20.000"))
        )
