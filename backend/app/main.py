"""
FraudLens — FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    print(f"\U0001f680 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"\U0001f4cd Environment: {settings.ENVIRONMENT}")

    # Redis
    try:
        redis_client = aioredis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        app.state.redis = redis_client
        print("\u2705 Redis connected")
    except Exception as e:
        print(f"\u274c Redis connection failed: {e}")
        app.state.redis = None

    # PostgreSQL
    try:
        from sqlalchemy import text
        from app.db.session import engine

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("\u2705 PostgreSQL connected")
    except Exception as e:
        print(f"\u274c PostgreSQL connection failed: {e}")

    app.state.started_at = datetime.now(timezone.utc)

    yield

    if app.state.redis:
        await app.state.redis.close()
        print("\U0001f50c Redis connection closed")
    print(f"\U0001f44b {settings.APP_NAME} shut down")


# ── Create App ───────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Real-time fraud detection engine — See fraud before it strikes.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ─────────────────────────────────────
from app.api.health import router as health_router
from app.api.transactions import router as transactions_router
from app.api.feedback import router as feedback_router
from app.api.analytics import router as analytics_router
from app.api.alerts import router as alerts_router
from app.api.model_health import router as model_health_router
from app.api.websocket import router as websocket_router

app.include_router(health_router)
app.include_router(transactions_router)
app.include_router(feedback_router)
app.include_router(analytics_router)
app.include_router(alerts_router)
app.include_router(model_health_router)
app.include_router(websocket_router)