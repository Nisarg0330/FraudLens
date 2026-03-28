"""
FraudLens — Analytics & alerts schemas.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel


# ── Dashboard summary ────────────────────────────────────
class CategoryCount(BaseModel):
    category: str
    count: int
    percentage: float


class DecisionBreakdown(BaseModel):
    approve: int
    review: int
    block: int


class AnalyticsSummaryResponse(BaseModel):
    """GET /api/v1/analytics/summary — dashboard overview metrics."""
    period: str
    total_transactions: int
    total_flagged: int
    total_blocked: int
    fraud_rate: float
    false_positive_rate: float
    avg_scoring_latency_ms: int
    p95_scoring_latency_ms: int
    p99_scoring_latency_ms: int
    transactions_per_second: int
    model_version: str
    decision_breakdown: DecisionBreakdown
    top_fraud_categories: list[CategoryCount]


# ── Trend data point ─────────────────────────────────────
class TrendDataPoint(BaseModel):
    timestamp: datetime
    total_transactions: int
    fraud_count: int
    fraud_rate: float
    avg_score: float
    avg_latency_ms: int
    blocked_count: int
    review_count: int


class AnalyticsTrendsResponse(BaseModel):
    """GET /api/v1/analytics/trends — time-series data."""
    period: str
    interval: str
    data_points: list[TrendDataPoint]


# ── Geographic fraud data ────────────────────────────────
class FraudLocation(BaseModel):
    latitude: float
    longitude: float
    fraud_score: float
    transaction_id: uuid.UUID
    amount: float
    merchant_name: str
    decision: str
    created_at: datetime


class HeatmapPoint(BaseModel):
    latitude: float
    longitude: float
    weight: float


class AnalyticsGeoResponse(BaseModel):
    """GET /api/v1/analytics/geo — fraud map data."""
    period: str
    fraud_locations: list[FraudLocation]
    heatmap_data: list[HeatmapPoint]


# ── Alerts ───────────────────────────────────────────────
class AlertItem(BaseModel):
    """Single alert in the analyst queue."""
    alert_id: str
    transaction_id: uuid.UUID
    fraud_score: float
    decision: str
    amount: float
    merchant_name: str
    user_name: str | None = None
    status: str  # pending, acknowledged, resolved
    priority: str  # low, medium, high, critical
    created_at: datetime


class AlertUpdateRequest(BaseModel):
    """PATCH /api/v1/alerts/{id} — update alert status."""
    status: str  # acknowledged, resolved


# ── Model health ─────────────────────────────────────────
class InferenceStats(BaseModel):
    avg_latency_ms: int
    p95_latency_ms: int
    p99_latency_ms: int
    total_scored_today: int


class ModelHealthMetrics(BaseModel):
    auroc: float
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float


class ModelHealthResponse(BaseModel):
    """GET /api/v1/model/health — current model status."""
    current_version: str
    deployed_at: datetime
    metrics: ModelHealthMetrics
    training_data_size: int
    last_retrained: datetime
    inference_stats: InferenceStats


# ── WebSocket message types ──────────────────────────────
class WSTransactionMessage(BaseModel):
    """WebSocket message pushed for each scored transaction."""
    type: str = "transaction"
    data: dict


class WSAlertMessage(BaseModel):
    """WebSocket message pushed for new fraud alerts."""
    type: str = "alert"
    data: dict