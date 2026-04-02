"""
FraudLens — Analytics & Model Health Endpoints
Powers the dashboard charts, summary stats, and geographic heatmap.
"""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.transaction import Transaction

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


# ── Helper: Parse Period ─────────────────────────────────
def _get_start_time(period: str) -> datetime:
    """Convert period string to a start datetime."""
    now = datetime.now(timezone.utc)
    mapping = {
        "1h": timedelta(hours=1),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
    }
    delta = mapping.get(period, timedelta(hours=24))
    return now - delta


# ── Dashboard Summary ────────────────────────────────────
@router.get("/summary")
async def analytics_summary(
    period: str = Query("24h", description="1h, 24h, 7d, or 30d"),
    db: AsyncSession = Depends(get_db),
):
    """
    Dashboard overview metrics.
    Deep's frontend calls this to populate the stats bar and summary cards.
    """
    start_time = _get_start_time(period)

    # Total transactions in period
    total_result = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.created_at >= start_time
        )
    )
    total = total_result.scalar() or 0

    # Decision breakdown
    decision_result = await db.execute(
        select(
            Transaction.decision,
            func.count(Transaction.id),
        )
        .where(Transaction.created_at >= start_time)
        .where(Transaction.decision.isnot(None))
        .group_by(Transaction.decision)
    )
    decisions = {row[0]: row[1] for row in decision_result}

    approve_count = decisions.get("APPROVE", 0)
    review_count = decisions.get("REVIEW", 0)
    block_count = decisions.get("BLOCK", 0)

    # Fraud rate
    flagged = review_count + block_count
    fraud_rate = round(flagged / total, 4) if total > 0 else 0

    # Latency stats
    latency_result = await db.execute(
        select(
            func.avg(Transaction.scoring_latency_ms),
            func.percentile_cont(0.95).within_group(Transaction.scoring_latency_ms),
            func.percentile_cont(0.99).within_group(Transaction.scoring_latency_ms),
        ).where(
            and_(
                Transaction.created_at >= start_time,
                Transaction.scoring_latency_ms.isnot(None),
            )
        )
    )
    latency_row = latency_result.one_or_none()
    avg_latency = int(latency_row[0]) if latency_row and latency_row[0] else 0
    p95_latency = int(latency_row[1]) if latency_row and latency_row[1] else 0
    p99_latency = int(latency_row[2]) if latency_row and latency_row[2] else 0

    # False positive rate (feedback-based)
    false_alarm_result = await db.execute(
        select(func.count(Transaction.id)).where(
            and_(
                Transaction.created_at >= start_time,
                Transaction.is_fraud == False,
                Transaction.decision.in_(["REVIEW", "BLOCK"]),
            )
        )
    )
    false_alarms = false_alarm_result.scalar() or 0
    fpr = round(false_alarms / flagged, 4) if flagged > 0 else 0

    # TPS calculation
    period_mapping = {"1h": 3600, "24h": 86400, "7d": 604800, "30d": 2592000}
    period_seconds = period_mapping.get(period, 86400)
    tps = int(total / period_seconds) if period_seconds > 0 else 0

    # Top fraud categories
    cat_result = await db.execute(
        select(
            Transaction.merchant_category,
            func.count(Transaction.id).label("count"),
        )
        .where(
            and_(
                Transaction.created_at >= start_time,
                Transaction.decision.in_(["REVIEW", "BLOCK"]),
            )
        )
        .group_by(Transaction.merchant_category)
        .order_by(func.count(Transaction.id).desc())
        .limit(5)
    )
    categories = []
    for row in cat_result:
        categories.append({
            "category": row[0],
            "count": row[1],
            "percentage": round(row[1] / flagged, 3) if flagged > 0 else 0,
        })

    return {
        "period": period,
        "total_transactions": total,
        "total_flagged": flagged,
        "total_blocked": block_count,
        "fraud_rate": fraud_rate,
        "false_positive_rate": fpr,
        "avg_scoring_latency_ms": avg_latency,
        "p95_scoring_latency_ms": p95_latency,
        "p99_scoring_latency_ms": p99_latency,
        "transactions_per_second": tps,
        "model_version": "v1.0.0-rules",
        "decision_breakdown": {
            "approve": approve_count,
            "review": review_count,
            "block": block_count,
        },
        "top_fraud_categories": categories,
    }


# ── Trend Data ───────────────────────────────────────────
@router.get("/trends")
async def analytics_trends(
    period: str = Query("7d", description="24h, 7d, or 30d"),
    interval: str = Query("1h", description="15m, 1h, or 1d"),
    db: AsyncSession = Depends(get_db),
):
    """
    Time-series data for fraud rate trends.
    Deep's frontend uses this for the line charts on the analytics page.
    """
    start_time = _get_start_time(period)

    # Map interval to PostgreSQL date_trunc
    trunc_map = {"15m": "hour", "1h": "hour", "1d": "day"}
    trunc_val = trunc_map.get(interval, "hour")

    result = await db.execute(
        select(
            func.date_trunc(trunc_val, Transaction.created_at).label("bucket"),
            func.count(Transaction.id).label("total"),
            func.count(case((Transaction.decision.in_(["REVIEW", "BLOCK"]), 1))).label("fraud_count"),
            func.avg(Transaction.fraud_score).label("avg_score"),
            func.avg(Transaction.scoring_latency_ms).label("avg_latency"),
            func.count(case((Transaction.decision == "BLOCK", 1))).label("blocked"),
            func.count(case((Transaction.decision == "REVIEW", 1))).label("review"),
        )
        .where(Transaction.created_at >= start_time)
        .group_by("bucket")
        .order_by("bucket")
    )

    data_points = []
    for row in result:
        total = row.total or 0
        fraud = row.fraud_count or 0
        data_points.append({
            "timestamp": row.bucket.isoformat() if row.bucket else None,
            "total_transactions": total,
            "fraud_count": fraud,
            "fraud_rate": round(fraud / total, 4) if total > 0 else 0,
            "avg_score": round(float(row.avg_score), 4) if row.avg_score else 0,
            "avg_latency_ms": int(row.avg_latency) if row.avg_latency else 0,
            "blocked_count": row.blocked or 0,
            "review_count": row.review or 0,
        })

    return {
        "period": period,
        "interval": interval,
        "data_points": data_points,
    }


# ── Geographic Fraud Data ────────────────────────────────
@router.get("/geo")
async def analytics_geo(
    period: str = Query("24h", description="Time range"),
    min_score: float = Query(0.3, ge=0, le=1, description="Minimum fraud score"),
    db: AsyncSession = Depends(get_db),
):
    """
    Geographic fraud distribution for the heatmap.
    Deep's frontend uses this to render the Mapbox fraud heatmap.
    """
    start_time = _get_start_time(period)

    # Individual fraud locations
    result = await db.execute(
        select(Transaction)
        .where(
            and_(
                Transaction.created_at >= start_time,
                Transaction.fraud_score >= min_score,
                Transaction.fraud_score.isnot(None),
            )
        )
        .order_by(Transaction.fraud_score.desc())
        .limit(500)
    )
    transactions = result.scalars().all()

    fraud_locations = []
    for t in transactions:
        fraud_locations.append({
            "latitude": t.latitude,
            "longitude": t.longitude,
            "fraud_score": t.fraud_score,
            "transaction_id": str(t.id),
            "amount": t.amount,
            "merchant_name": t.merchant_name,
            "decision": t.decision,
            "created_at": t.created_at.isoformat(),
        })

    # Heatmap aggregation (group by rounded lat/lon)
    heatmap_result = await db.execute(
        select(
            func.round(Transaction.latitude, 1).label("lat"),
            func.round(Transaction.longitude, 1).label("lon"),
            func.count(Transaction.id).label("weight"),
        )
        .where(
            and_(
                Transaction.created_at >= start_time,
                Transaction.fraud_score >= min_score,
                Transaction.fraud_score.isnot(None),
            )
        )
        .group_by("lat", "lon")
    )

    heatmap_data = []
    for row in heatmap_result:
        heatmap_data.append({
            "latitude": float(row.lat),
            "longitude": float(row.lon),
            "weight": row.weight,
        })

    return {
        "period": period,
        "fraud_locations": fraud_locations,
        "heatmap_data": heatmap_data,
    }