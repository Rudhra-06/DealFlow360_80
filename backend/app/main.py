from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router

app = FastAPI(
    title="DealFlow360 API",
    description="Intelligent B2B Sales Operations Platform Backend API",
    version="1.0.0",
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root-level health endpoint
@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify backend status."""
    return {
        "status": "healthy",
        "service": "DealFlow360 API"
    }

@app.on_event("startup")
async def startup_event():
    """Auto-initialize database schema and seed demo records if database is empty."""
    try:
        from app.db.session import engine
        from app.db.base import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        from app.db.session import AsyncSessionLocal
        from sqlalchemy import select
        from app.models.user import User
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(User).limit(1))
            if not res.scalar_one_or_none():
                from scripts.bootstrap_full_demo import bootstrap_demo
                await bootstrap_demo()
    except Exception as e:
        print(f"[DealFlow360 Startup] Notice: {e}")

# Include API v1 router
app.include_router(api_router, prefix="/api/v1")
