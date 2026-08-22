from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


class StrategyFamily(str, Enum):
    MARKET_STRUCTURE = "MARKET_STRUCTURE"
    SMART_MONEY = "SMART_MONEY"
    LIQUIDITY = "LIQUIDITY"
    ICT_SESSION = "ICT_SESSION"
    TREND = "TREND"
    MOMENTUM = "MOMENTUM"
    MEAN_REVERSION = "MEAN_REVERSION"
    BREAKOUT = "BREAKOUT"
    VWAP = "VWAP"
    MULTI_TIMEFRAME = "MULTI_TIMEFRAME"


@dataclass
class StrategyVote:
    family: StrategyFamily
    direction: str  # "BUY", "SELL", "NEUTRAL"
    confidence: float  # 0.0 to 1.0
    quality: float  # 0.0 to 1.0
    regime_suitability: float  # 0.0 to 1.0
    evidence: List[str] = field(default_factory=list)
    cluster: str = "DEFAULT"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "family": self.family.value,
            "direction": self.direction,
            "confidence": round(float(self.confidence), 3),
            "quality": round(float(self.quality), 3),
            "regime_suitability": round(float(self.regime_suitability), 3),
            "evidence": self.evidence,
            "cluster": self.cluster
        }


@dataclass
class EnsembleDecision:
    direction: str  # "BUY", "SELL", "NEUTRAL"
    ensemble_confidence: float  # 0.0 to 1.0
    ensemble_score: float  # 0 to 100
    buy_weight: float
    sell_weight: float
    neutral_weight: float
    participating_strategies: int
    agreed_strategies: List[str]
    conflicted_strategies: List[str]
    collinearity_dampener_applied: float
    votes: List[StrategyVote] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "direction": self.direction,
            "ensemble_confidence": round(float(self.ensemble_confidence), 3),
            "ensemble_score": round(float(self.ensemble_score), 2),
            "buy_weight": round(float(self.buy_weight), 3),
            "sell_weight": round(float(self.sell_weight), 3),
            "neutral_weight": round(float(self.neutral_weight), 3),
            "participating_strategies": self.participating_strategies,
            "agreed_strategies": self.agreed_strategies,
            "conflicted_strategies": self.conflicted_strategies,
            "collinearity_dampener_applied": round(float(self.collinearity_dampener_applied), 3),
            "votes": [v.to_dict() for v in self.votes],
            "details": self.details
        }
