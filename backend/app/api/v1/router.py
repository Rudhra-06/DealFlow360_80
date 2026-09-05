from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.approval_policies import router as approval_policies_router
from app.api.v1.auth import auth_router
from app.api.v1.billing_plans import router as billing_plans_router
from app.api.v1.customer_tiers import router as customer_tiers_router
from app.api.v1.customers import router as customers_router
from app.api.v1.discount_policies import router as discount_policies_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.product_categories import router as product_categories_router
from app.api.v1.products import router as products_router
from app.api.v1.quotations import router as quotations_router
from app.api.v1.recommendation_rules import router as recommendation_rules_router
from app.api.v1.warehouses import router as warehouses_router
from app.db.session import get_db

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(customer_tiers_router, prefix="/customer-tiers", tags=["Customer Tiers"])
api_router.include_router(customers_router, prefix="/customers", tags=["Customers"])
api_router.include_router(product_categories_router, prefix="/product-categories", tags=["Product Categories"])
api_router.include_router(products_router, prefix="/products", tags=["Products"])
api_router.include_router(warehouses_router, prefix="/warehouses", tags=["Warehouses"])
api_router.include_router(inventory_router, prefix="/inventory", tags=["Inventory"])
api_router.include_router(discount_policies_router, prefix="/discount-policies", tags=["Discount Policies"])
api_router.include_router(approval_policies_router, prefix="/approval-policies", tags=["Approval Policies"])
api_router.include_router(billing_plans_router, prefix="/billing-plans", tags=["Billing Plans"])
api_router.include_router(quotations_router, prefix="/quotations", tags=["Quotations"])
api_router.include_router(recommendation_rules_router, prefix="/recommendation-rules", tags=["Recommendation Rules"])




@api_router.get("/health", tags=["Health"])
def health_check_v1():
    """Health check endpoint for API v1."""
    return {
        "status": "healthy",
        "service": "DealFlow360 API"
    }


@api_router.get("/health/db", tags=["Health"])
async def health_check_db(db: AsyncSession = Depends(get_db)):
    """Database connectivity health check endpoint."""
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            return {
                "status": "healthy",
                "database": "connected"
            }
        raise Exception("Unexpected query result")
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "detail": "Database connection unavailable"
            }
        )
