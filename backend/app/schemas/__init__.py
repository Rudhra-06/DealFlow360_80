"""Pydantic request and response schemas package."""

from app.schemas.approval_policy import ApprovalPolicyCreate, ApprovalPolicyRead, ApprovalPolicyUpdate
from app.schemas.auth import LoginRequest, TokenPayload, TokenResponse
from app.schemas.billing_plan import BillingPlanCreate, BillingPlanRead, BillingPlanUpdate
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from app.schemas.customer_tier import CustomerTierCreate, CustomerTierRead, CustomerTierUpdate
from app.schemas.discount_policy import (
    DiscountPolicyCreate,
    DiscountPolicyRead,
    DiscountPolicyResolutionRead,
    DiscountPolicyUpdate,
)
from app.schemas.inventory import InventoryCreate, InventoryRead, InventoryUpdate
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.schemas.product_category import ProductCategoryCreate, ProductCategoryRead, ProductCategoryUpdate
from app.schemas.role import RoleBase, RoleCreateInternal, RoleRead
from app.schemas.user import UserBase, UserCreateInternal, UserRead
from app.schemas.warehouse import WarehouseCreate, WarehouseRead, WarehouseUpdate

__all__ = [
    "LoginRequest",
    "TokenPayload",
    "TokenResponse",
    "RoleBase",
    "RoleCreateInternal",
    "RoleRead",
    "UserBase",
    "UserCreateInternal",
    "UserRead",
    "CustomerTierCreate",
    "CustomerTierUpdate",
    "CustomerTierRead",
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerRead",
    "ProductCategoryCreate",
    "ProductCategoryUpdate",
    "ProductCategoryRead",
    "ProductCreate",
    "ProductUpdate",
    "ProductRead",
    "WarehouseCreate",
    "WarehouseUpdate",
    "WarehouseRead",
    "InventoryCreate",
    "InventoryUpdate",
    "InventoryRead",
    "DiscountPolicyCreate",
    "DiscountPolicyUpdate",
    "DiscountPolicyRead",
    "DiscountPolicyResolutionRead",
    "ApprovalPolicyCreate",
    "ApprovalPolicyUpdate",
    "ApprovalPolicyRead",
    "BillingPlanCreate",
    "BillingPlanUpdate",
    "BillingPlanRead",
]
