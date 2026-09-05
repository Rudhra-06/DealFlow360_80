import uuid
from decimal import Decimal
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.product_category import ProductCategoryCreate, ProductCategoryUpdate
from app.services.exceptions import (
    DuplicateResourceError,
    InactiveReferenceError,
    InvalidReferenceError,
    ResourceNotFoundError,
)
from app.services.product import ProductService
from app.services.product_category import ProductCategoryService


@pytest.mark.anyio
async def test_product_category_service_crud(db_session: AsyncSession):
    service = ProductCategoryService(db_session)
    name = f"CAT_{uuid.uuid4().hex[:6]}"

    cat = await service.create_category(ProductCategoryCreate(name=name, description="Hardware Cat"))
    assert cat.id is not None
    assert cat.name == name

    fetched = await service.get_category_by_id(cat.id)
    assert fetched.name == name

    # Duplicate name raises error
    with pytest.raises(DuplicateResourceError):
        await service.create_category(ProductCategoryCreate(name=name))


@pytest.mark.anyio
async def test_product_service_crud_and_decimal_pricing(db_session: AsyncSession):
    cat_service = ProductCategoryService(db_session)
    cat = await cat_service.create_category(
        ProductCategoryCreate(name=f"CAT_PROD_{uuid.uuid4().hex[:6]}")
    )

    prod_service = ProductService(db_session)
    uid = uuid.uuid4().hex[:6]

    prod_in = ProductCreate(
        sku=f"  sku-{uid}  ",
        name="Enterprise Server Unit",
        category_id=cat.id,
        list_price=Decimal("1299.99"),
        cost_price=Decimal("850.50"),
        currency="usd",
        unit_of_measure="ea",
    )

    prod = await prod_service.create_product(prod_in)
    assert prod.id is not None
    assert prod.sku == f"SKU-{uid.upper()}"
    assert prod.list_price == Decimal("1299.99")
    assert prod.cost_price == Decimal("850.50")
    assert prod.currency == "USD"
    assert prod.unit_of_measure == "EA"
    assert prod.category.id == cat.id

    # Duplicate SKU raises error
    with pytest.raises(DuplicateResourceError):
        await prod_service.create_product(
            ProductCreate(
                sku=f"sku-{uid}",
                name="Duplicate SKU Product",
                category_id=cat.id,
            )
        )


@pytest.mark.anyio
async def test_product_inactive_category_validation(db_session: AsyncSession):
    cat_service = ProductCategoryService(db_session)
    cat = await cat_service.create_category(
        ProductCategoryCreate(name=f"INACT_CAT_{uuid.uuid4().hex[:6]}", is_active=False)
    )

    prod_service = ProductService(db_session)

    with pytest.raises(InactiveReferenceError):
        await prod_service.create_product(
            ProductCreate(
                sku=f"SKU-INACT-{uuid.uuid4().hex[:6]}",
                name="Inactive Category Prod",
                category_id=cat.id,
            )
        )
