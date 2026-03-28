"""
FraudLens — Analyst feedback schemas.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── What the analyst sends ───────────────────────────────
class FeedbackRequest(BaseModel):
    """POST /api/v1/feedback — analyst submits verdict on a flagged transaction."""
    transaction_id: uuid.UUID
    verdict: str = Field(
        description="confirmed_fraud, false_alarm, or escalated"
    )
    notes: str | None = None


# ── What the backend returns ─────────────────────────────
class FeedbackResponse(BaseModel):
    """POST /api/v1/feedback — confirmation response."""
    feedback_id: int
    transaction_id: uuid.UUID
    verdict: str
    reviewed_at: datetime