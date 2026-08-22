from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "TradeSignalAI-v3"
    VERSION: str = "3.0.0"
    API_V1_STR: str = "/api/v1"

    ENVIRONMENT: str = "development"
    EXECUTION_MODE: str = "DEMO"
    AUTO_TRADING_ENABLED: bool = True
    EMERGENCY_KILL_SWITCH: bool = False
    DEBUG: bool = True

    MAX_DAILY_LOSS_PCT: float = 3.0
    MAX_DRAWDOWN_PCT: float = 10.0
    MIN_AI_CONFIDENCE: float = 0.65

    DATABASE_URL: str | None = None
    REDIS_URL: str | None = None
    VECTOR_DB_URL: str | None = None

    SECRET_KEY: str | None = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    RATE_LIMIT_PER_MINUTE: int = 60

    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    OPENAI_API_KEY: str | None = None
    OPENAI_DEFAULT_MODEL: str = "gpt-4o"

    BINANCE_API_KEY: str | None = None
    BINANCE_SECRET_KEY: str | None = None
    
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_DEFAULT_MODEL: str = "anthropic/claude-3-opus"

    TV_USERNAME: str | None = None
    TV_PASSWORD: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()