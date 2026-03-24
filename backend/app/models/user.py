"""
FraudLens — User Model
Synthetic customer profiles with spending patterns.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    # ── Location ─────────────────────────────────────────
    home_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    home_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    home_country: Mapped[str] = mapped_column(String(2), nullable=False, default="CA")

    # ── Profile ──────────────────────────────────────────
    avg_transaction_amount: Mapped[float] = mapped_column(Float, nullable=False)
    risk_profile: Mapped[str] = mapped_column(
        String(20), nullable=False, default="low"
    )  # low, medium, high
    profile_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="professional"
    )  # student, professional, business_traveler, retiree, affluent
    account_age_days: Mapped[int] = mapped_column(Integer, nullable=False, default=365)

    # ── Timestamps ───────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<User {self.name} ({self.profile_type})>"