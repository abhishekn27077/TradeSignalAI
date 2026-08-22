from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


class DataQualityState(str, Enum):
    DATA_QUALITY_GOOD = "DATA_QUALITY_GOOD"
    DATA_QUALITY_DEGRADED = "DATA_QUALITY_DEGRADED"
    DATA_STALE = "DATA_STALE"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
    DATA_CORRUPTED = "DATA_CORRUPTED"


@dataclass
class QualityIssue:
    issue_type: str
    severity: str  # "WARNING", "CRITICAL", "FATAL"
    message: str
    candle_index: Optional[int] = None
    timestamp: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataQualityReport:
    asset: str
    timeframe: str
    total_candles_checked: int
    state: DataQualityState
    is_valid_for_trading: bool
    issues: List[QualityIssue] = field(default_factory=list)
    last_candle_time_utc: Optional[str] = None
    freshness_seconds: Optional[float] = None
    provider: str = "UNKNOWN"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "timeframe": self.timeframe,
            "total_candles_checked": self.total_candles_checked,
            "state": self.state.value,
            "is_valid_for_trading": self.is_valid_for_trading,
            "issues_count": len(self.issues),
            "issues": [
                {
                    "issue_type": i.issue_type,
                    "severity": i.severity,
                    "message": i.message,
                    "candle_index": i.candle_index,
                    "timestamp": i.timestamp,
                    "details": i.details,
                }
                for i in self.issues
            ],
            "last_candle_time_utc": self.last_candle_time_utc,
            "freshness_seconds": self.freshness_seconds,
            "provider": self.provider,
            "metadata": self.metadata,
        }
