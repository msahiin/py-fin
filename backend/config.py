"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application
    APP_NAME: str = "Trading Platform"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]

    # Database
    DATABASE_URL: str = "postgresql://trading_user:trading_pass@localhost:5432/trading_db"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

    # Celery
    CELERY_BROKER_URL: str = REDIS_URL
    CELERY_RESULT_BACKEND: str = REDIS_URL

    # Exchange API Keys (will be loaded from .env)
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""

    # Data Collection
    DATA_UPDATE_INTERVAL: int = 60  # seconds
    SUPPORTED_SYMBOLS: List[str] = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT",
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"
    ]

    # ML Models
    MODEL_RETRAIN_INTERVAL: int = 86400  # 24 hours in seconds
    LSTM_SEQUENCE_LENGTH: int = 60
    PREDICTION_CONFIDENCE_THRESHOLD: float = 0.75

    # Trading
    MAX_POSITION_SIZE: float = 0.1  # 10% of capital
    RISK_PER_TRADE: float = 0.02  # 2% of capital
    MAX_OPEN_POSITIONS: int = 5
    DEFAULT_LEVERAGE: int = 1

    # Backtesting
    BACKTEST_COMMISSION: float = 0.001  # 0.1%
    BACKTEST_SLIPPAGE: float = 0.0005  # 0.05%

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
