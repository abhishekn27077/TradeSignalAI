from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    request_id: str
    symbol: str
    timeframe: str
    forecast_horizon: int = Field(..., description="Number of periods (candles) to forecast ahead")
    
    market_regime: str | None = None
    
    # Context data (not saved to DB, just passed in memory)
    historical_data: list[dict[str, Any]] | None = None
    feature_data: list[dict[str, Any]] | None = None


class ForecastResult(BaseModel):
    model_id: str
    
    # Required outputs
    direction: str = Field(..., description="BULLISH, BEARISH, NEUTRAL")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score from 0 to 1")
    
    # Optional/Advanced outputs
    expected_move_pct: float | None = None
    expected_volatility: float | None = None
    expected_hold_candles: int | None = None
    probability: float | None = Field(None, ge=0.0, le=1.0)
    
    reasoning_metadata: dict[str, Any] = Field(default_factory=dict)
    
    prediction_timestamp: datetime = Field(default_factory=datetime.utcnow)
    expiry_timestamp: datetime | None = None


class ForecastConsensus(BaseModel):
    combined_direction: str
    combined_confidence: float
    combined_probability: float | None = None
    
    expected_move_pct: float | None = None
    expected_volatility: float | None = None
    expected_hold_candles: float | None = None
    
    weights_used: dict[str, float]
    models_included: int
