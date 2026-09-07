from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_SECRET_KEYS = {
    "secret",
    "changeme",
    "development-secret",
    "test-secret",
    "12345678",
    "default-secret",
    "password",
    "admin",
}


class Settings(BaseSettings):
    PROJECT_NAME: str = "TradeSignalAI-v3"
    VERSION: str = "3.0.0"
    API_V1_STR: str = "/api/v1"

    ENVIRONMENT: str = "development"
    EXECUTION_MODE: str = "DEMO"
    REAL_MONEY_ENABLED: bool = False
    BROKER_EXECUTION_ENABLED: bool = False
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

    # API keys for admin endpoints — loaded from env, never hardcoded
    VALID_API_KEYS: list[str] = []

    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 3600

    # AI & LLM Provider API Keys
    OPENAI_API_KEY: str | None = None
    OPENAI_DEFAULT_MODEL: str = "gpt-4o"

    GEMINI_API_KEY: str | None = None

    NVIDIA_API_KEY: str | None = None

    BINANCE_API_KEY: str | None = None
    BINANCE_SECRET_KEY: str | None = None
    
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_DEFAULT_MODEL: str = "anthropic/claude-3-opus"

    # MetaTrader 5 Integration Credentials
    MT5_LOGIN: str | None = None
    MT5_PASSWORD: str | None = None
    MT5_SERVER: str | None = None
    MT5_PATH: str | None = None

    TV_USERNAME: str | None = None
    TV_PASSWORD: str | None = None

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        env_lower = self.ENVIRONMENT.lower().strip()
        if env_lower in ("production", "prod"):
            # Mandatory secret verification in production — FAIL CLOSED
            if not self.SECRET_KEY or not self.SECRET_KEY.strip():
                raise ValueError(
                    "CRITICAL: Production startup aborted: SECRET_KEY must be provided via environment variables."
                )
            if self.SECRET_KEY.strip().lower() in INSECURE_SECRET_KEYS or len(self.SECRET_KEY.strip()) < 32:
                raise ValueError(
                    "CRITICAL: Production startup aborted: SECRET_KEY is insecure or too short (minimum 32 characters required)."
                )
            # Ensure real-money lockout unless explicitly verified
            if self.REAL_MONEY_ENABLED and not self.BROKER_EXECUTION_ENABLED:
                raise ValueError(
                    "CRITICAL: Inconsistent execution configuration: REAL_MONEY_ENABLED without BROKER_EXECUTION_ENABLED."
                )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()