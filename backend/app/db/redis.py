"""
FraudLens — Redis Connection Manager
Handles connection to Redis for streams, caching, and feature store.
"""

import redis.asyncio as aioredis

from app.config import settings


# ── Redis Client ─────────────────────────────────────────
async def get_redis() -> aioredis.Redis:
    """
    Create and return a Redis connection.
    Used as a FastAPI dependency or called directly.
    """
    return aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )