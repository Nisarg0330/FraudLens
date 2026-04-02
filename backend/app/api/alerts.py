"""
FraudLens — Alert Management Endpoints
Manages the analyst alert queue for flagged transactions.
"""

import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.transaction import Transaction
from app.models.user import User

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])


@router.get("")
async def list_alerts(
    status: str = Query("pending", description="pending, acknowledged, or resolved"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Get fraud alerts for the analyst queue.
    Alerts are transactions with REVIEW or BLOCK decisions.
    Sorted by fraud score (highest first).
    """
    # Build base query — REVIEW and BLOCK transactions are alerts
    base_filter = and_(
        Transaction.decision.in_(["REVIEW", "BLOCK"]),
        Transaction.fraud_score.isnot(None),
    )

    # For now, "pending" = no feedback yet, "resolved" = has feedback
    if status == "pending":
        base_filter = and_(base_filter, Transaction.is_fraud.is_(None))
    elif status == "resolved":
        base_filter = and_(base_filter, Transaction.is_fraud.isnot(None))

    # Count
    count_result = await db.execute(
        select(func.count(Transaction.id)).where(base_filter)
    )
    total = count_result.scalar() or 0

    # Get alerts
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Transaction)
        .where(base_filter)
        .order_by(desc(Transaction.fraud_score))
        .offset(offset)
        .limit(page_size)
    )
    transactions = result.scalars().all()

    # Get user names
    user_ids = list(set(t.user_id for t in transactions))
    user_names = {}
    if user_ids:
        users_result = await db.execute(
            select(User.id, User.name).where(User.id.in_(user_ids))
        )
        user_names = {row.id: row.name for row in users_result}

    # Build response
    data = []
    for t in transactions:
        # Determine priority based on fraud score
        if t.fraud_score >= 0.8:
            priority = "critical"
        elif t.fraud_score >= 0.6:
            priority = "high"
        elif t.fraud_score >= 0.4:
            priority = "medium"
        else:
            priority = "low"

        # Determine alert status
        if t.is_fraud is None:
            alert_status = "pending"
        else:
            alert_status = "resolved"

        data.append({
            "alert_id": str(t.id),
            "transaction_id": str(t.id),
            "fraud_score": t.fraud_score,
            "decision": t.decision,
            "amount": t.amount,
            "merchant_name": t.merchant_name,
            "user_name": user_names.get(t.user_id),
            "status": alert_status,
            "priority": priority,
            "created_at": t.created_at.isoformat(),
        })

    total_pages = (total + page_size - 1) // page_size

    return {
        "data": data,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.patch("/{alert_id}")
async def update_alert(
    alert_id: uuid.UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    Update alert status (acknowledge or resolve).
    """
    result = await db.execute(
        select(Transaction).where(Transaction.id == alert_id)
    )
    txn = result.scalar_one_or_none()

    if not txn:
        raise HTTPException(status_code=404, detail="Alert not found")

    new_status = body.get("status")
    if new_status not in ["acknowledged", "resolved"]:
        raise HTTPException(status_code=422, detail="Status must be 'acknowledged' or 'resolved'")

    return {
        "alert_id": str(txn.id),
        "status": new_status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }