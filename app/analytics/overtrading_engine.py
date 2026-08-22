import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class OvertradingReport:
    asset: str
    is_overtrading_detected: bool
    signals_last_24h: int
    rapid_reentry_count: int
    signals_in_current_session: int
    recommended_cooldown_minutes: int
    clustering_risk_level: str  # "LOW", "MODERATE", "HIGH"
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "is_overtrading_detected": self.is_overtrading_detected,
            "signals_last_24h": self.signals_last_24h,
            "rapid_reentry_count": self.rapid_reentry_count,
            "signals_in_current_session": self.signals_in_current_session,
            "recommended_cooldown_minutes": self.recommended_cooldown_minutes,
            "clustering_risk_level": self.clustering_risk_level,
            "details": self.details
        }


class OvertradingDetector:
    """
    Overtrading & Signal Clustering Detection Engine.
    Prevents repeated rapid re-entries, revenge-like signal generation, and excessive session churn.
    """

    def __init__(
        self,
        max_signals_per_session: int = 4,
        max_signals_per_day: int = 8,
        min_reentry_bars_cooldown: int = 3
    ):
        self.max_signals_per_session = max_signals_per_session
        self.max_signals_per_day = max_signals_per_day
        self.min_reentry_bars_cooldown = min_reentry_bars_cooldown

    def evaluate_overtrading(
        self,
        recent_signals: List[Dict[str, Any]],
        asset: str = "EURUSD",
        current_time_utc: Optional[datetime] = None
    ) -> OvertradingReport:
        if not recent_signals:
            return OvertradingReport(
                asset=asset,
                is_overtrading_detected=False,
                signals_last_24h=0,
                rapid_reentry_count=0,
                signals_in_current_session=0,
                recommended_cooldown_minutes=0,
                clustering_risk_level="LOW"
            )

        now_utc = current_time_utc or datetime.now(timezone.utc)
        cutoff_24h = now_utc - timedelta(hours=24)
        cutoff_session = now_utc - timedelta(hours=4)

        sig_24h = 0
        sig_session = 0
        rapid_reentries = 0

        # Sort signals by timestamp
        sorted_sigs = sorted(
            recent_signals,
            key=lambda s: pd.to_datetime(s.get("timestamp_utc", s.get("timestamp", now_utc)), utc=True)
        )

        for i, s in enumerate(sorted_sigs):
            ts = pd.to_datetime(s.get("timestamp_utc", s.get("timestamp", now_utc)), utc=True)
            if ts >= cutoff_24h:
                sig_24h += 1
            if ts >= cutoff_session:
                sig_session += 1

            # Check rapid re-entry distance to previous signal
            if i > 0:
                prev_ts = pd.to_datetime(sorted_sigs[i-1].get("timestamp_utc", sorted_sigs[i-1].get("timestamp", now_utc)), utc=True)
                delta_min = (ts - prev_ts).total_seconds() / 60.0
                if delta_min < 45.0:  # Less than 45 minutes between signals on same asset
                    rapid_reentries += 1

        is_overtrading = (sig_session >= self.max_signals_per_session) or (sig_24h >= self.max_signals_per_day) or (rapid_reentries >= 2)

        if is_overtrading:
            risk_level = "HIGH"
            cooldown_min = 60
        elif sig_session >= 3 or rapid_reentries >= 1:
            risk_level = "MODERATE"
            cooldown_min = 30
        else:
            risk_level = "LOW"
            cooldown_min = 0

        return OvertradingReport(
            asset=asset,
            is_overtrading_detected=is_overtrading,
            signals_last_24h=sig_24h,
            rapid_reentry_count=rapid_reentries,
            signals_in_current_session=sig_session,
            recommended_cooldown_minutes=cooldown_min,
            clustering_risk_level=risk_level,
            details={
                "max_signals_per_session": self.max_signals_per_session,
                "max_signals_per_day": self.max_signals_per_day
            }
        )
