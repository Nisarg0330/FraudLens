"""
FraudLens — Shared schemas used across multiple endpoints.
"""

from pydantic import BaseModel


class PaginatedResponse(BaseModel):
    """Standard pagination wrapper for all list endpoints."""
    total: int
    page: int
    page_size: int
    total_pages: int


class HealthResponse(BaseModel):
    """Response from /api/v1/health endpoint."""
    status: str
    version: str
    environment: str
    services: dict[str, str]
    uptime_seconds: int