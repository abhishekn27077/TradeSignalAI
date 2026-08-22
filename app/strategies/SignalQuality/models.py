from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


class SignalGrade(str, Enum):
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    NO_TRADE = "NO_TRADE"


class NoTradeReason(str, Enum):
    DATA_STALE = "DATA_STALE"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
    DATA_CORRUPTED = "DATA_CORRUPTED"
    HIGH_SPREAD = "HIGH_SPREAD"
    LOW_LIQUIDITY = "LOW_LIQUIDITY"
    CONFLICTING_STRUCTURE = "CONFLICTING_STRUCTURE"
    NO_HTF_ALIGNMENT = "NO_HTF_ALIGNMENT"
    LOW_CONFLUENCE = "LOW_CONFLUENCE"
    POOR_RR = "POOR_RR"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    EVENT_RISK = "EVENT_RISK"
    ENTRY_EXPIRED = "ENTRY_EXPIRED"
    SIGNAL_INVALIDATED = "SIGNAL_INVALIDATED"
    PORTFOLIO_RISK = "PORTFOLIO_RISK"
    CORRELATED_EXPOSURE = "CORRELATED_EXPOSURE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass
class SignalQualityEvaluation:
    asset: str
    grade: SignalGrade
    is_actionable: bool
    quality_score: float  # 0 to 100
    rejection_reasons: List[NoTradeReason] = field(default_factory=list)
    rejection_messages: List[str] = field(default_factory=list)
    risk_reward_ratio: float = 0.0
    confluence_score: float = 0.0
    htf_aligned: bool = False
    data_quality_healthy: bool = True
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "grade": self.grade.value,
            "is_actionable": self.is_actionable,
            "quality_score": round(float(self.quality_score), 2),
            "rejection_reasons": [r.value for r in self.rejection_reasons],
            "rejection_messages": self.rejection_messages,
            "risk_reward_ratio": round(float(self.risk_reward_ratio), 2),
            "confluence_score": round(float(self.confluence_score), 2),
            "htf_aligned": self.htf_aligned,
            "data_quality_healthy": self.data_quality_healthy,
            "details": self.details
        }
