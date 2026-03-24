"""
FraudLens — Analyst Feedback & Model Metrics Models
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AnalystFeedback(Base):
    __tablename__ = "analyst_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    analyst_id: Mapped[str] = mapped_column(
        String(100), nullable=False, default="analyst_1"
    )

    # ── Verdict ──────────────────────────────────────────
    verdict: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # confirmed_fraud, false_alarm, escalated
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Timestamps ───────────────────────────────────────
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Feedback txn={self.transaction_id} → {self.verdict}>"


class ModelMetrics(Base):
    __tablename__ = "model_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)

    # ── Performance Metrics ──────────────────────────────
    auroc: Mapped[float] = mapped_column(Float, nullable=False)
    precision_score: Mapped[float] = mapped_column(Float, nullable=False)
    recall_score: Mapped[float] = mapped_column(Float, nullable=False)
    f1_score: Mapped[float] = mapped_column(Float, nullable=False)
    false_positive_rate: Mapped[float] = mapped_column(Float, nullable=False)

    # ── Evaluation Info ──────────────────────────────────
    threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)

    # ── Timestamps ───────────────────────────────────────
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<ModelMetrics {self.model_version} AUROC={self.auroc}>"