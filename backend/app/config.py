"""
FraudLens — Application Configuration
Loads settings from environment variables / .env file
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "FraudLens"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    APP_DEBUG: bool = True
    API_KEY: str = "dev-api-key-change-in-production"

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://fraudlens:localdev123@localhost:5432/fraudlens"

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── ML ───────────────────────────────────────────────
    MODEL_VERSION: str = "v1.0.0"
    ONNX_MODEL_PATH: str = "./ml_models/onnx/"

    # ── Scoring Thresholds ───────────────────────────────
    THRESHOLD_APPROVE: float = 0.3
    THRESHOLD_BLOCK: float = 0.7

    model_config = {
        "env_file": "../.env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Single instance used across the app
settings = Settings()
