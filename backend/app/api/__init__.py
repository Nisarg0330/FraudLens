"""
FraudLens — API Routes
"""

from app.api.health import router as health_router
from app.api.transactions import router as transactions_router
from app.api.feedback import router as feedback_router

__all__ = ["health_router", "transactions_router", "feedback_router"]