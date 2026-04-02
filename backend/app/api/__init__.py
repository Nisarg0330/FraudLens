"""
FraudLens — API Routes
"""

from app.api.health import router as health_router
from app.api.transactions import router as transactions_router
from app.api.feedback import router as feedback_router
from app.api.analytics import router as analytics_router
from app.api.alerts import router as alerts_router
from app.api.model_health import router as model_health_router
from app.api.websocket import router as websocket_router

__all__ = [
    "health_router",
    "transactions_router",
    "feedback_router",
    "analytics_router",
    "alerts_router",
    "model_health_router",
    "websocket_router",
]