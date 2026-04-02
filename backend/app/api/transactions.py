"""
FraudLens — Transaction API Endpoints
Handles listing, detail view, scoring, and SHAP explanations.
"""

import uuid
import time
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.redis import get_redis
from app.models.user import User
from app.models.transaction import Transaction
from app.services.feature_service import FeatureService
from app.schemas.transaction import (
    TransactionScoreRequest,
    TransactionScoreResponse,
    TransactionListItem,
    TransactionDetailResponse,
    TransactionExplainResponse,
    ShapFeature,
    UserProfile,
    RecentTransaction,
)

router = APIRouter(prefix="/api/v1/transactions", tags=["Transactions"])


# ── List Transactions ────────────────────────────────────
@router.get("")
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    decision: str | None = Query(None, description="APPROVE, REVIEW, or BLOCK"),
    min_score: float | None = Query(None, ge=0, le=1),
    max_score: float | None = Query(None, ge=0, le=1),
    merchant_category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="asc or desc"),
    db: AsyncSession = Depends(get_db),
):
    """
    List transactions with filtering, sorting, and pagination.
    Deep's frontend calls this to populate the live feed table.
    """
    # Build query
    query = select(Transaction)
    count_query = select(func.count(Transaction.id))

    # Apply filters
    if decision:
        query = query.where(Transaction.decision == decision.upper())
        count_query = count_query.where(Transaction.decision == decision.upper())
    if min_score is not None:
        query = query.where(Transaction.fraud_score >= min_score)
        count_query = count_query.where(Transaction.fraud_score >= min_score)
    if max_score is not None:
        query = query.where(Transaction.fraud_score <= max_score)
        count_query = count_query.where(Transaction.fraud_score <= max_score)
    if merchant_category:
        query = query.where(Transaction.merchant_category == merchant_category)
        count_query = count_query.where(Transaction.merchant_category == merchant_category)
    if start_date:
        query = query.where(Transaction.created_at >= start_date)
        count_query = count_query.where(Transaction.created_at >= start_date)
    if end_date:
        query = query.where(Transaction.created_at <= end_date)
        count_query = count_query.where(Transaction.created_at <= end_date)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply sorting
    sort_column = getattr(Transaction, sort_by, Transaction.created_at)
    if sort_order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute
    result = await db.execute(query)
    transactions = result.scalars().all()

    # Get user names for each transaction
    user_ids = list(set(t.user_id for t in transactions))
    if user_ids:
        users_result = await db.execute(
            select(User.id, User.name).where(User.id.in_(user_ids))
        )
        user_names = {row.id: row.name for row in users_result}
    else:
        user_names = {}

    # Build response
    data = []
    for t in transactions:
        data.append(TransactionListItem(
            transaction_id=t.id,
            user_id=t.user_id,
            user_name=user_names.get(t.user_id),
            amount=t.amount,
            currency=t.currency,
            merchant_name=t.merchant_name,
            merchant_category=t.merchant_category,
            card_type=t.card_type,
            latitude=t.latitude,
            longitude=t.longitude,
            country_code=t.country_code,
            is_online=t.is_online,
            fraud_score=t.fraud_score,
            decision=t.decision,
            is_fraud=t.is_fraud,
            scoring_latency_ms=t.scoring_latency_ms,
            created_at=t.created_at,
        ))

    total_pages = (total + page_size - 1) // page_size

    return {
        "data": data,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# ── Get Transaction Detail ───────────────────────────────
@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get full details for a single transaction.
    Includes SHAP values, model scores, user profile, and recent history.
    Deep's frontend calls this when an analyst clicks on a transaction.
    """
    # Get transaction
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id)
    )
    txn = result.scalar_one_or_none()

    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Get user profile
    user_result = await db.execute(
        select(User).where(User.id == txn.user_id)
    )
    user = user_result.scalar_one_or_none()

    user_profile = None
    if user:
        user_profile = UserProfile(
            home_city=f"{user.home_country}",
            account_age_days=user.account_age_days,
            avg_transaction_amount=user.avg_transaction_amount,
            risk_profile=user.risk_profile,
        )

    # Get recent transactions for this user (last 10)
    recent_result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == txn.user_id)
        .where(Transaction.id != txn.id)
        .order_by(desc(Transaction.created_at))
        .limit(10)
    )
    recent_txns = recent_result.scalars().all()

    recent = [
        RecentTransaction(
            transaction_id=r.id,
            amount=r.amount,
            merchant_name=r.merchant_name,
            fraud_score=r.fraud_score,
            decision=r.decision,
            created_at=r.created_at,
        )
        for r in recent_txns
    ]

    # Parse SHAP values
    shap_features = None
    if txn.shap_values:
        shap_data = txn.shap_values if isinstance(txn.shap_values, list) else []
        shap_features = [ShapFeature(**s) for s in shap_data]

    return TransactionDetailResponse(
        transaction_id=txn.id,
        user_id=txn.user_id,
        user_name=user.name if user else None,
        amount=txn.amount,
        currency=txn.currency,
        merchant_name=txn.merchant_name,
        merchant_category=txn.merchant_category,
        card_type=txn.card_type,
        latitude=txn.latitude,
        longitude=txn.longitude,
        country_code=txn.country_code,
        is_online=txn.is_online,
        fraud_score=txn.fraud_score,
        decision=txn.decision,
        is_fraud=txn.is_fraud,
        model_scores=txn.model_scores,
        top_shap_features=shap_features,
        model_version=txn.model_version,
        scoring_latency_ms=txn.scoring_latency_ms,
        created_at=txn.created_at,
        user_profile=user_profile,
        recent_transactions=recent,
    )


# ── Get SHAP Explanation ─────────────────────────────────
@router.get("/{transaction_id}/explain")
async def explain_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed SHAP explanation for a scored transaction.
    Shows exactly which features pushed the fraud score up or down.
    """
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id)
    )
    txn = result.scalar_one_or_none()

    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if txn.fraud_score is None:
        raise HTTPException(status_code=400, detail="Transaction has not been scored yet")

    # Parse SHAP values
    shap_features = []
    if txn.shap_values:
        shap_data = txn.shap_values if isinstance(txn.shap_values, list) else []
        shap_features = [ShapFeature(**s) for s in shap_data]

    return TransactionExplainResponse(
        transaction_id=txn.id,
        fraud_score=txn.fraud_score,
        base_score=0.0043,  # Will be real when ML models are trained
        shap_features=shap_features,
        model_version=txn.model_version or "v1.0.0",
    )


# ── Score Transaction ────────────────────────────────────
@router.post("/score")
async def score_transaction(
    request: TransactionScoreRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Score a single transaction in real-time.
    For now, uses a simple rule-based placeholder.
    Will be replaced with real ML ensemble in Week 3-4.
    """
    start_time = time.time()

    # Get user for context
    user_result = await db.execute(
        select(User).where(User.id == request.user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ── Placeholder scoring (will be replaced by ML) ─────
    # Simple rule-based scoring to test the pipeline
    score = 0.05  # Base score (low risk)
    shap_features = []

    # Rule 1: High amount relative to user average
    amount_ratio = request.amount / max(user.avg_transaction_amount, 1)
    if amount_ratio > 5:
        score += 0.3
        shap_features.append({
            "feature": "amount_vs_avg_ratio",
            "impact": 0.3,
            "value": round(amount_ratio, 2),
            "description": f"Amount is {amount_ratio:.1f}x the user average",
        })
    elif amount_ratio > 2:
        score += 0.1
        shap_features.append({
            "feature": "amount_vs_avg_ratio",
            "impact": 0.1,
            "value": round(amount_ratio, 2),
            "description": f"Amount is {amount_ratio:.1f}x the user average",
        })

    # Rule 2: Foreign transaction
    if request.country_code != user.home_country:
        score += 0.2
        shap_features.append({
            "feature": "foreign_transaction",
            "impact": 0.2,
            "value": 1.0,
            "description": f"Transaction in {request.country_code}, user home is {user.home_country}",
        })

    # Rule 3: Online + high amount
    if request.is_online and request.amount > 500:
        score += 0.15
        shap_features.append({
            "feature": "online_high_amount",
            "impact": 0.15,
            "value": request.amount,
            "description": f"Online transaction of ${request.amount:.2f}",
        })

    # Rule 4: Geo distance from home
    from app.services.feature_service import FeatureService
    distance = FeatureService._haversine(
        user.home_latitude, user.home_longitude,
        request.latitude, request.longitude,
    )
    if distance > 500:
        score += 0.25
        shap_features.append({
            "feature": "geo_distance_from_home",
            "impact": 0.25,
            "value": round(distance, 2),
            "description": f"{distance:.0f}km from home location",
        })

    # Cap score at 1.0
    score = min(score, 1.0)
    score = round(score, 4)

    # Determine decision
    if score < 0.3:
        decision = "APPROVE"
    elif score < 0.7:
        decision = "REVIEW"
    else:
        decision = "BLOCK"

    scoring_latency = int((time.time() - start_time) * 1000)

    # Placeholder model scores (will be real in Week 3-4)
    model_scores = {
        "lightgbm": round(score * 1.05, 4),
        "autoencoder": round(score * 0.95, 4),
        "isolation_forest": round(score * 0.90, 4),
    }

    # Save to database
    txn = Transaction(
        id=uuid.uuid4(),
        user_id=request.user_id,
        amount=request.amount,
        currency=request.currency,
        merchant_name=request.merchant_name,
        merchant_category=request.merchant_category,
        card_type=request.card_type,
        latitude=request.latitude,
        longitude=request.longitude,
        country_code=request.country_code,
        is_online=request.is_online,
        fraud_score=score,
        decision=decision,
        model_scores=model_scores,
        shap_values=shap_features,
        model_version="v1.0.0-rules",
        scoring_latency_ms=scoring_latency,
    )
    db.add(txn)
    await db.flush()

    return TransactionScoreResponse(
        transaction_id=txn.id,
        fraud_score=score,
        decision=decision,
        model_scores=model_scores,
        top_shap_features=[ShapFeature(**s) for s in shap_features],
        scoring_latency_ms=scoring_latency,
        model_version="v1.0.0-rules",
        created_at=txn.created_at,
    )