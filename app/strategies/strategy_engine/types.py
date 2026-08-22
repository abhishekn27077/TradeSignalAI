from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class SignalDirection(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"

class Timeframe(str, Enum):
    M1 = "1m"
    M5 = "5M"
    M15 = "15M"
    M30 = "30M"
    H1 = "1H"
    H4 = "4H"
    D1 = "1D"
    W1 = "1W"
    MN1 = "1M"

class SignalStrength(str, Enum):
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class StrategySignal(BaseModel):
    """
    Standardized signal format required by the Phase 5 instructions.
    Strategies ONLY output this model. They NEVER execute trades.
    """
    signal_id: str
    strategy_name: str
    asset: str
    timeframe: Timeframe
    direction: SignalDirection
    
    confidence: float = Field(..., ge=0.0, le=1.0)
    strength: SignalStrength
    risk_level: RiskLevel
    reasoning: str
    
    supporting_indicators: list[str] = []
    
    entry_zone: list[float] | None = None # [min_entry, max_entry]
    stop_loss_suggestion: float | None = None
    take_profit_suggestion: float | None = None
    invalidation_level: float | None = None
    
    # Phase 1: Decision Intelligence Fields
    trade_quality: str | None = Field(default="N/A", description="e.g. A+, B, C")
    expected_move_pct: float | None = None
    expected_hold_hours: float | None = None
    market_regime: str | None = None
    volatility_pct: float | None = None
    trend_strength: float | None = None
    session: str | None = None
    ai_consensus: str | None = None
    historical_similars: int | None = 0
    win_rate_similars: float | None = 0.0
    risk_reward_ratio: float | None = None
    reasons_against: list[str] = []
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
