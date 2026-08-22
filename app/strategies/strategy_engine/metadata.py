from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class StrategyCategory(str, Enum):
    TREND_FOLLOWING = "Trend Following"
    MOMENTUM = "Momentum"
    MEAN_REVERSION = "Mean Reversion"
    BREAKOUT = "Breakout"
    SMART_MONEY = "Smart Money"
    OSCILLATOR = "Oscillator"
    VOLATILITY = "Volatility"
    PATTERN = "Pattern"
    HYBRID = "Hybrid"


class StrategyStatus(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    PAUSED = "PAUSED"


class MarketRegime(str, Enum):
    TRENDING = "Trending"
    STRONG_TRENDING = "Strong Trending"
    RANGE = "Range"
    BREAKOUT = "Breakout"
    LOW_VOLATILITY = "Low Volatility"
    HIGH_VOLATILITY = "High Volatility"
    NEWS_EVENT = "News Event"
    HOLIDAY = "Holiday"


class RiskProfile(str, Enum):
    VERY_LOW = "Very Low"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    VERY_HIGH = "Very High"


class StrategyMetadata(BaseModel):
    name: str
    description: str
    version: str = "1.0.0"
    category: StrategyCategory
    supported_assets: list[str] = Field(default_factory=lambda: ["forex", "crypto", "indices"])
    supported_timeframes: list[str] = Field(default_factory=lambda: ["1H", "4H", "1D"])
    supported_regimes: list[MarketRegime] = Field(default_factory=lambda: [m for m in MarketRegime])
    entry_rules: list[str] = Field(default_factory=list)
    exit_rules: list[str] = Field(default_factory=list)
    required_indicators: list[str] = Field(default_factory=list)
    risk_profile: RiskProfile = RiskProfile.MEDIUM
    status: StrategyStatus = StrategyStatus.ENABLED
    priority: int = 5
    weight: float = 1.0
    max_concurrent_trades: int = 3
    daily_trade_limit: int = 10
    allowed_sessions: list[str] = Field(default_factory=lambda: ["london", "new_york", "asia", "all"])
    allowed_assets: list[str] = Field(default_factory=lambda: ["all"])
    allowed_timeframes: list[str] = Field(default_factory=lambda: ["all"])
    min_trade_quality: int = 60
    min_ai_confidence: float = 0.5
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def dict_full(self) -> dict[str, Any]:
        return self.model_dump()
