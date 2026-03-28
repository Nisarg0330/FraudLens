"""
FraudLens — Real-Time Feature Store
Computes and caches user behavioral features in Redis.

These features are what the ML models use to detect fraud:
- How many transactions has this user made in the last hour?
- What's their average spend in the last 24 hours?
- How far is this transaction from their last one?

Redis stores "hot" features (recent, fast access).
PostgreSQL stores "cold" features (historical, for retraining).
"""

import json
import math
from datetime import datetime, timezone

from redis.asyncio import Redis


class FeatureService:
    """Manages real-time user features in Redis."""

    def __init__(self, redis: Redis):
        self.redis = redis

    # ── Key Patterns ─────────────────────────────────────
    # features:{user_id}:1h    → 1-hour rolling window
    # features:{user_id}:24h   → 24-hour rolling window
    # features:{user_id}:7d    → 7-day rolling window
    # features:{user_id}:last  → last transaction details

    def _key(self, user_id: str, window: str) -> str:
        return f"features:{user_id}:{window}"

    # ── Get Features ─────────────────────────────────────
    async def get_user_features(self, user_id: str) -> dict:
        """
        Retrieve all cached features for a user.
        Returns empty defaults if user has no history yet.
        """
        features = {}

        # Get rolling window features (1h, 24h, 7d)
        for window in ["1h", "24h", "7d"]:
            key = self._key(user_id, window)
            data = await self.redis.hgetall(key)
            if data:
                features[f"txn_count_{window}"] = float(data.get("count", 0))
                features[f"txn_sum_{window}"] = float(data.get("sum", 0))
                features[f"txn_avg_{window}"] = float(data.get("avg", 0))
                features[f"txn_max_{window}"] = float(data.get("max", 0))
            else:
                features[f"txn_count_{window}"] = 0
                features[f"txn_sum_{window}"] = 0
                features[f"txn_avg_{window}"] = 0
                features[f"txn_max_{window}"] = 0

        # Get last transaction details
        last_key = self._key(user_id, "last")
        last_data = await self.redis.hgetall(last_key)
        if last_data:
            features["last_txn_amount"] = float(last_data.get("amount", 0))
            features["last_txn_lat"] = float(last_data.get("latitude", 0))
            features["last_txn_lon"] = float(last_data.get("longitude", 0))
            features["last_txn_timestamp"] = last_data.get("timestamp", "")
        else:
            features["last_txn_amount"] = 0
            features["last_txn_lat"] = 0
            features["last_txn_lon"] = 0
            features["last_txn_timestamp"] = ""

        return features

    # ── Update Features ──────────────────────────────────
    async def update_user_features(
        self,
        user_id: str,
        amount: float,
        latitude: float,
        longitude: float,
    ) -> dict:
        """
        Update rolling window features after a new transaction.
        Called every time a transaction is scored.
        Returns the updated features.
        """
        now = datetime.now(timezone.utc).isoformat()

        # Update each rolling window
        for window, ttl_seconds in [("1h", 7200), ("24h", 172800), ("7d", 1209600)]:
            key = self._key(user_id, window)
            existing = await self.redis.hgetall(key)

            count = float(existing.get("count", 0)) + 1
            total = float(existing.get("sum", 0)) + amount
            avg = total / count if count > 0 else 0
            current_max = float(existing.get("max", 0))
            new_max = max(current_max, amount)

            await self.redis.hset(key, mapping={
                "count": str(count),
                "sum": str(round(total, 2)),
                "avg": str(round(avg, 2)),
                "max": str(round(new_max, 2)),
            })
            await self.redis.expire(key, ttl_seconds)

        # Update last transaction
        last_key = self._key(user_id, "last")
        await self.redis.hset(last_key, mapping={
            "amount": str(amount),
            "latitude": str(latitude),
            "longitude": str(longitude),
            "timestamp": now,
        })
        await self.redis.expire(last_key, 2592000)  # 30 days

        return await self.get_user_features(user_id)

    # ── Compute Derived Features ─────────────────────────
    async def compute_transaction_features(
        self,
        user_id: str,
        amount: float,
        latitude: float,
        longitude: float,
        avg_transaction_amount: float,
    ) -> dict:
        """
        Compute all features for a single transaction.
        Combines cached rolling features with computed features
        like geo_velocity and amount_vs_avg_ratio.
        """
        # Get cached features first
        features = await self.get_user_features(user_id)

        # ── Amount-based features ────────────────────────
        if avg_transaction_amount > 0:
            features["amount_vs_avg_ratio"] = round(
                amount / avg_transaction_amount, 2
            )
        else:
            features["amount_vs_avg_ratio"] = 1.0

        avg_24h = features.get("txn_avg_24h", 0)
        if avg_24h > 0:
            features["amount_zscore"] = round(
                (amount - avg_24h) / max(avg_24h * 0.5, 1), 2
            )
        else:
            features["amount_zscore"] = 0

        # ── Geo features ─────────────────────────────────
        last_lat = features.get("last_txn_lat", 0)
        last_lon = features.get("last_txn_lon", 0)
        last_ts = features.get("last_txn_timestamp", "")

        if last_lat and last_lon and last_ts:
            distance_km = self._haversine(
                last_lat, last_lon, latitude, longitude
            )
            features["geo_distance_from_last"] = round(distance_km, 2)

            # Calculate velocity (km/h)
            try:
                last_time = datetime.fromisoformat(last_ts)
                now = datetime.now(timezone.utc)
                hours = (now - last_time).total_seconds() / 3600
                if hours > 0:
                    features["geo_velocity"] = round(distance_km / hours, 2)
                else:
                    features["geo_velocity"] = 0
            except (ValueError, TypeError):
                features["geo_velocity"] = 0
        else:
            features["geo_distance_from_last"] = 0
            features["geo_velocity"] = 0

        # ── Update features after computation ────────────
        await self.update_user_features(user_id, amount, latitude, longitude)

        return features

    # ── Haversine Formula ────────────────────────────────
    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance in km between two lat/lon points.
        Used to compute geo_velocity (if you traveled 3000km in 10 minutes,
        that's physically impossible = strong fraud signal).
        """
        R = 6371  # Earth's radius in km
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))
        return R * c