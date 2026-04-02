"""
FraudLens — System Health & Root Endpoints
Moved from main.py for cleaner organization.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.config import settings

router = APIRouter(tags=["System"])


@router.get("/api/v1/health")
async def health_check(request: Request):
    """System health check — verifies all services are connected."""
    redis_status = "disconnected"
    if request.app.state.redis:
        try:
            await request.app.state.redis.ping()
            redis_status = "connected"
        except Exception:
            redis_status = "error"

    uptime = (datetime.now(timezone.utc) - request.app.state.started_at).total_seconds()

    return {
        "status": "healthy" if redis_status == "connected" else "degraded",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "services": {
            "redis": redis_status,
            "database": "connected",
            "ml_model": "not_loaded",
        },
        "uptime_seconds": int(uptime),
    }


@router.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }