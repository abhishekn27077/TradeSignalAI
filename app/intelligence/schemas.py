from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class NewsAssessment(BaseModel):
    sentiment: Literal["BULLISH", "BEARISH", "NEUTRAL"]
    impact: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    affected_assets: List[str]
    time_horizon: Literal["INTRADAY", "H4", "DAILY", "SWING"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str

class MarketContextAssessment(BaseModel):
    asset: str
    directional_bias: Literal["BULLISH", "BEARISH", "NEUTRAL"]
    sentiment: float = Field(ge=0.0, le=1.0)
    impact: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    time_horizon: Literal["INTRADAY", "H4", "DAILY", "SWING"]
    supporting_factors: List[str]
    contradicting_factors: List[str]
    event_risk: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    recommendation: Literal["SUPPORT", "CAUTION", "NO_TRADE"]

class ContradictionAssessment(BaseModel):
    agreement_score: float = Field(ge=0.0, le=1.0)
    contradiction_score: float = Field(ge=0.0, le=1.0)
    reasons: List[str]

class RiskAssessment(BaseModel):
    risk_flags: List[str]
    veto_trade: bool
