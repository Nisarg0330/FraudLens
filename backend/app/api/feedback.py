"""
FraudLens — Analyst Feedback Endpoints
Handles analyst verdicts on flagged transactions.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.transaction import Transaction
from app.models.feedback import AnalystFeedback
from app.schemas.feedback import FeedbackRequest, FeedbackResponse

router = APIRouter(prefix="/api/v1/feedback", tags=["Feedback"])


@router.post("", status_code=201)
async def submit_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit analyst verdict on a flagged transaction.
    Updates the transaction's is_fraud field based on the verdict.
    This data feeds back into model retraining.
    """
    # Verify transaction exists
    txn_result = await db.execute(
        select(Transaction).where(Transaction.id == request.transaction_id)
    )
    txn = txn_result.scalar_one_or_none()

    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Validate verdict
    valid_verdicts = ["confirmed_fraud", "false_alarm", "escalated"]
    if request.verdict not in valid_verdicts:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid verdict. Must be one of: {valid_verdicts}",
        )

    # Create feedback record
    feedback = AnalystFeedback(
        transaction_id=request.transaction_id,
        verdict=request.verdict,
        notes=request.notes,
    )
    db.add(feedback)

    # Update transaction ground truth
    if request.verdict == "confirmed_fraud":
        txn.is_fraud = True
    elif request.verdict == "false_alarm":
        txn.is_fraud = False

    await db.flush()

    return FeedbackResponse(
        feedback_id=feedback.id,
        transaction_id=feedback.transaction_id,
        verdict=feedback.verdict,
        reviewed_at=feedback.reviewed_at,
    )