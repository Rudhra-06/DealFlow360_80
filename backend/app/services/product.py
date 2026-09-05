from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories.product import ProductRepository
from app.repositories.product_category import ProductCategoryRepository
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.exceptions import (
    DuplicateResourceError,
    InactiveReferenceError,
    InvalidReferenceError,
    ResourceNotFoundError,
)


class ProductService:
    def __init__(self, db: AsyncSession) -> None:
        self.db: AsyncSession = db
        self.product_repo: ProductRepository = ProductRepository()
        self.category_repo: ProductCategoryRepository = ProductCategoryRepository()

    async def get_product_by_id(self, product_id: int) -> Product:
        product = await self.product_repo.get_by_id_with_category(self.db, product_id)
        if not product:
            raise ResourceNotFoundError(f"Product with ID {product_id} not found.")
        return product

    async def list_products(
        self,
        category_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Product]:
        return await self.product_repo.list_products(
            self.db,
            category_id=category_id,
            is_active=is_active,
            search=search,
            limit=limit,
            offset=offset,
        )

    async def create_product(self, data: ProductCreate) -> Product:
        # 1. SKU Normalization
        sku_clean = data.sku.strip().upper()
        existing_sku = await self.product_repo.get_by_sku(self.db, sku_clean)
        if existing_sku:
            raise DuplicateResourceError(f"Product with SKU '{sku_clean}' already exists.")

        # 2. Category Validation
        category = await self.category_repo.get_by_id(self.db, data.category_id)
        if not category:
            raise InvalidReferenceError(f"ProductCategory with ID {data.category_id} does not exist.")
        if not category.is_active:
            raise InactiveReferenceError(f"Cannot assign product to inactive ProductCategory '{category.name}'.")

        # 3. Currency and UOM Normalization
        currency_clean = data.currency.strip().upper()
        uom_clean = data.unit_of_measure.strip().upper()

        product = Product(
            sku=sku_clean,
            name=data.name.strip(),
            description=data.description.strip() if data.description else None,
            category_id=data.category_id,
            list_price=data.list_price,
            cost_price=data.cost_price,
            currency=currency_clean,
            unit_of_measure=uom_clean,
            is_active=data.is_active,
        )

        await self.product_repo.add(self.db, product)

        try:
            await self.db.commit()
            return await self.get_product_by_id(product.id)
        except Exception:
            await self.db.rollback()
            raise

    async def update_product(self, product_id: int, data: ProductUpdate) -> Product:
        product = await self.get_product_by_id(product_id)
        update_dict = data.model_dump(exclude_unset=True)

        if "sku" in update_dict and update_dict["sku"] is not None:
            sku_clean = update_dict["sku"].strip().upper()
            if sku_clean != product.sku:
                existing = await self.product_repo.get_by_sku(self.db, sku_clean)
                if existing:
                    raise DuplicateResourceError(f"Product with SKU '{sku_clean}' already exists.")
                product.sku = sku_clean

        if "category_id" in update_dict and update_dict["category_id"] is not None:
            cat_id = update_dict["category_id"]
            if cat_id != product.category_id:
                cat = await self.category_repo.get_by_id(self.db, cat_id)
                if not cat:
                    raise InvalidReferenceError(f"ProductCategory with ID {cat_id} does not exist.")
                if not cat.is_active:
                    raise InactiveReferenceError(f"Cannot assign product to inactive ProductCategory '{cat.name}'.")
                product.category_id = cat_id

        if "name" in update_dict and update_dict["name"] is not None:
            product.name = update_dict["name"].strip()
        if "description" in update_dict:
            product.description = update_dict["description"].strip() if update_dict["description"] else None
        if "list_price" in update_dict and update_dict["list_price"] is not None:
            product.list_price = update_dict["list_price"]
        if "cost_price" in update_dict and update_dict["cost_price"] is not None:
            product.cost_price = update_dict["cost_price"]
        if "currency" in update_dict and update_dict["currency"] is not None:
            product.currency = update_dict["currency"].strip().upper()
        if "unit_of_measure" in update_dict and update_dict["unit_of_measure"] is not None:
            product.unit_of_measure = update_dict["unit_of_measure"].strip().upper()
        if "is_active" in update_dict and update_dict["is_active"] is not None:
            product.is_active = update_dict["is_active"]

        try:
            await self.db.commit()
            return await self.get_product_by_id(product.id)
        except Exception:
            await self.db.rollback()
            raise
