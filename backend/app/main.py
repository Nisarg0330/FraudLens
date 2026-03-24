"""
FraudLens — FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.session import engine


# ── Lifespan (startup / shutdown) ────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup and shutdown.
    Startup: verify database and Redis connections.
    Shutdown: close connections cleanly.
    """
    # ── Startup ──────────────────────────────────────────
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📍 Environment: {settings.ENVIRONMENT}")

    # Test Redis connection
    try:
        redis_client = aioredis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        app.state.redis = redis_client
        print("✅ Redis connected")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        app.state.redis = None

    # Store startup time for uptime tracking
    app.state.started_at = datetime.now(timezone.utc)

    # Test Database connection
    try:
        from sqlalchemy import text

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("✅ PostgreSQL connected")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")

    yield

    # ── Shutdown ─────────────────────────────────────────
    if app.state.redis:
        await app.state.redis.close()
        print("🔌 Redis connection closed")

    print(f"👋 {settings.APP_NAME} shut down")


# ── Create App ───────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Real-time fraud detection engine — See fraud before it strikes.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS (allow frontend to connect) ────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health Check ─────────────────────────────────────────
@app.get("/api/v1/health", tags=["System"])
async def health_check():
    """
    System health check — verifies all services are connected.
    No authentication required.
    """
    # Check Redis
    redis_status = "disconnected"
    if app.state.redis:
        try:
            await app.state.redis.ping()
            redis_status = "connected"
        except Exception:
            redis_status = "error"

    # Calculate uptime
    uptime = (datetime.now(timezone.utc) - app.state.started_at).total_seconds()

    return {
        "status": "healthy" if redis_status == "connected" else "degraded",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "services": {
            "redis": redis_status,
            "database": "connected",  # Will be added in Phase 2
            "ml_model": "not_loaded",  # Will be added in Phase 4
        },
        "uptime_seconds": int(uptime),
    }


# ── Root Redirect ────────────────────────────────────────
@app.get("/", tags=["System"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
