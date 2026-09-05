from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import auth_router
from app.db.session import get_db

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])


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
