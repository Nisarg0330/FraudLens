"""
FraudLens — Model Health Endpoint
Reports current ML model status and performance metrics.
"""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.transaction import Transaction

router = APIRouter(prefix="/api/v1/model", tags=["Model"])


@router.get("/health")
async def model_health(
    db: AsyncSession = Depends(get_db),
):
    """
    Current model version, performance metrics, and inference stats.
    Will show real metrics once ML models are trained in Week 3-4.
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Inference stats for today
    stats_result = await db.execute(
        select(
            func.avg(Transaction.scoring_latency_ms),
            func.percentile_cont(0.95).within_group(Transaction.scoring_latency_ms),
            func.percentile_cont(0.99).within_group(Transaction.scoring_latency_ms),
            func.count(Transaction.id),
        ).where(
            and_(
                Transaction.created_at >= today_start,
                Transaction.scoring_latency_ms.isnot(None),
            )
        )
    )
    row = stats_result.one_or_none()

    return {
        "current_version": "v1.0.0-rules",
        "deployed_at": "2026-03-23T10:00:00Z",
        "metrics": {
            "auroc": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "false_positive_rate": 0.0,
        },
        "training_data_size": 0,
        "last_retrained": "2026-03-23T08:00:00Z",
        "inference_stats": {
            "avg_latency_ms": int(row[0]) if row and row[0] else 0,
            "p95_latency_ms": int(row[1]) if row and row[1] else 0,
            "p99_latency_ms": int(row[2]) if row and row[2] else 0,
            "total_scored_today": row[3] if row and row[3] else 0,
        },
    }