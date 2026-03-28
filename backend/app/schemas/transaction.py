"""
FraudLens — Transaction request/response schemas.
These define the exact JSON shapes the API sends and receives.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── What the frontend sends to score a transaction ───────
class TransactionScoreRequest(BaseModel):
    """POST /api/v1/transactions/score — request body."""
    user_id: uuid.UUID
    amount: float = Field(gt=0, description="Transaction amount, must be positive")
    currency: str = Field(default="CAD", max_length=3)
    merchant_name: str = Field(max_length=255)
    merchant_category: str = Field(max_length=50)
    card_type: str = Field(description="visa, mastercard, amex, or debit")
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    country_code: str = Field(default="CA", max_length=2)
    is_online: bool = False


# ── SHAP feature explanation ─────────────────────────────
class ShapFeature(BaseModel):
    """Single SHAP feature contribution."""
    feature: str
    impact: float
    value: float
    description: str | None = None


# ── What the backend returns after scoring ───────────────
class TransactionScoreResponse(BaseModel):
    """POST /api/v1/transactions/score — response body."""
    transaction_id: uuid.UUID
    fraud_score: float
    decision: str  # APPROVE, REVIEW, BLOCK
    model_scores: dict[str, float]  # {"lightgbm": 0.91, ...}
    top_shap_features: list[ShapFeature]
    scoring_latency_ms: int
    model_version: str
    created_at: datetime


# ── Transaction in a list (lighter than full detail) ─────
class TransactionListItem(BaseModel):
    """Single item in GET /api/v1/transactions response."""
    transaction_id: uuid.UUID
    user_id: uuid.UUID
    user_name: str | None = None
    amount: float
    currency: str
    merchant_name: str
    merchant_category: str
    card_type: str
    latitude: float
    longitude: float
    country_code: str
    is_online: bool
    fraud_score: float | None
    decision: str | None
    is_fraud: bool | None
    scoring_latency_ms: int | None
    created_at: datetime


# ── Full transaction detail (includes SHAP + user info) ──
class UserProfile(BaseModel):
    """Embedded user profile in transaction detail."""
    home_city: str | None = None
    account_age_days: int
    avg_transaction_amount: float
    risk_profile: str


class RecentTransaction(BaseModel):
    """Lightweight transaction for the 'recent history' section."""
    transaction_id: uuid.UUID
    amount: float
    merchant_name: str
    fraud_score: float | None
    decision: str | None
    created_at: datetime


class TransactionDetailResponse(BaseModel):
    """GET /api/v1/transactions/{id} — full detail response."""
    transaction_id: uuid.UUID
    user_id: uuid.UUID
    user_name: str | None = None
    amount: float
    currency: str
    merchant_name: str
    merchant_category: str
    card_type: str
    latitude: float
    longitude: float
    country_code: str
    is_online: bool
    fraud_score: float | None
    decision: str | None
    is_fraud: bool | None
    model_scores: dict[str, float] | None
    top_shap_features: list[ShapFeature] | None
    model_version: str | None
    scoring_latency_ms: int | None
    created_at: datetime
    user_profile: UserProfile | None = None
    recent_transactions: list[RecentTransaction] = []


# ── SHAP explanation endpoint ────────────────────────────
class TransactionExplainResponse(BaseModel):
    """GET /api/v1/transactions/{id}/explain — SHAP breakdown."""
    transaction_id: uuid.UUID
    fraud_score: float
    base_score: float
    shap_features: list[ShapFeature]
    model_version: str