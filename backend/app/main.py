from fastapi import FastAPI
from app.api.v1.router import api_router

app = FastAPI(
    title="DealFlow360 API",
    description="Intelligent B2B Sales Operations Platform Backend API",
    version="1.0.0",
)

# Root-level health endpoint
@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify backend status."""
    return {
        "status": "healthy",
        "service": "DealFlow360 API"
    }

# Include API v1 router
app.include_router(api_router, prefix="/api/v1")
