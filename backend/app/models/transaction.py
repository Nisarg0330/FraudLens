"""
FraudLens — Transaction Model
Every transaction scored by the system.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )

    # ── Transaction Details ──────────────────────────────
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CAD")
    merchant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    merchant_category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    card_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # visa, mastercard, amex, debit

    # ── Location ─────────────────────────────────────────
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, default="CA")
    is_online: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── ML Scoring ───────────────────────────────────────
    fraud_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    decision: Mapped[str | None] = mapped_column(
        String(10), nullable=True, index=True
    )  # APPROVE, REVIEW, BLOCK
    is_fraud: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )  # Ground truth — set by analyst or simulation

    # ── Model Details ────────────────────────────────────
    model_scores: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )  # {"lightgbm": 0.91, "autoencoder": 0.85, "isolation_forest": 0.78}
    shap_values: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )  # Top SHAP features as JSON
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    scoring_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Timestamps ───────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    def __repr__(self) -> str:
        return f"<Transaction {self.id} ${self.amount} → {self.decision}>"