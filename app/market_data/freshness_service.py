"""
app/market_data/freshness_service.py
=====================================
Phase 8: Centralized Canonical Data Freshness Engine.

Central authority for evaluating market data timeliness across all providers,
asset classes, and timeframes.

Invariant:
STALE != VALID
UNAVAILABLE != VALID
EXPIRED != VALID
INVALID != VALID

If freshness_status is not FRESH, NO signal may be generated from this data.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger("freshness_service")


class FreshnessStatus(str, Enum):
    FRESH = "FRESH"
    STALE = "STALE"
    EXPIRED = "EXPIRED"
    UNAVAILABLE = "UNAVAILABLE"
    INVALID = "INVALID"


# Live tick freshness thresholds (milliseconds)
TICK_FRESHNESS_THRESHOLDS_MS: Dict[str, Dict[str, float]] = {
    "FOREX": {"fresh_limit_ms": 15000.0, "stale_limit_ms": 60000.0},
    "CRYPTO": {"fresh_limit_ms": 10000.0, "stale_limit_ms": 45000.0},
    "METALS": {"fresh_limit_ms": 20000.0, "stale_limit_ms": 60000.0},
    "INDEX": {"fresh_limit_ms": 20000.0, "stale_limit_ms": 60000.0},
}

# Closed-candle freshness thresholds (seconds from candle close time)
CANDLE_FRESHNESS_THRESHOLDS_SEC: Dict[str, Dict[str, float]] = {
    "M1": {"fresh_limit_sec": 120.0, "stale_limit_sec": 300.0},
    "M5": {"fresh_limit_sec": 600.0, "stale_limit_sec": 1200.0},
    "M15": {"fresh_limit_sec": 1800.0, "stale_limit_sec": 3600.0},
    "M30": {"fresh_limit_sec": 3600.0, "stale_limit_sec": 7200.0},
    "H1": {"fresh_limit_sec": 7200.0, "stale_limit_sec": 14400.0},
    "H4": {"fresh_limit_sec": 28800.0, "stale_limit_sec": 57600.0},
    "D1": {"fresh_limit_sec": 172800.0, "stale_limit_sec": 345600.0},
}


@dataclass(frozen=True)
class FreshnessResult:
    status: FreshnessStatus
    source_timestamp: str
    received_timestamp: str
    data_age_ms: float
    data_age_seconds: float
    max_tolerated_age_ms: float
    reason: str
    is_actionable: bool  # True ONLY if status == FreshnessStatus.FRESH

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "source_timestamp": self.source_timestamp,
            "received_timestamp": self.received_timestamp,
            "data_age_ms": round(self.data_age_ms, 2),
            "data_age_seconds": round(self.data_age_seconds, 2),
            "max_tolerated_age_ms": self.max_tolerated_age_ms,
            "reason": self.reason,
            "is_actionable": self.is_actionable,
        }


class DataFreshnessService:
    """
    Centralized freshness policy evaluator.
    """

    @classmethod
    def evaluate_tick_freshness(
        cls,
        source_timestamp: Optional[datetime],
        received_timestamp: Optional[datetime] = None,
        asset_class: str = "FOREX",
        reference_time: Optional[datetime] = None,
    ) -> FreshnessResult:
        """
        Evaluates the freshness of a live market tick / quote.
        """
        now = reference_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        rec_time = received_timestamp or now
        if rec_time.tzinfo is None:
            rec_time = rec_time.replace(tzinfo=timezone.utc)

        now_iso = now.isoformat()
        rec_iso = rec_time.isoformat()

        if source_timestamp is None:
            return FreshnessResult(
                status=FreshnessStatus.UNAVAILABLE,
                source_timestamp="UNKNOWN",
                received_timestamp=rec_iso,
                data_age_ms=-1.0,
                data_age_seconds=-1.0,
                max_tolerated_age_ms=10000.0,
                reason="MISSING_SOURCE_TIMESTAMP",
                is_actionable=False,
            )

        src_time = source_timestamp
        if src_time.tzinfo is None:
            src_time = src_time.replace(tzinfo=timezone.utc)

        src_iso = src_time.isoformat()

        age_delta = now - src_time
        age_ms = age_delta.total_seconds() * 1000.0
        age_sec = age_delta.total_seconds()

        if age_sec < -5.0:
            # Future timestamp > 5s indicates system clock skew or corrupted data
            return FreshnessResult(
                status=FreshnessStatus.INVALID,
                source_timestamp=src_iso,
                received_timestamp=rec_iso,
                data_age_ms=age_ms,
                data_age_seconds=age_sec,
                max_tolerated_age_ms=10000.0,
                reason="FUTURE_SOURCE_TIMESTAMP_CLOCK_SKEW",
                is_actionable=False,
            )

        thresholds = TICK_FRESHNESS_THRESHOLDS_MS.get(
            asset_class.upper(), TICK_FRESHNESS_THRESHOLDS_MS["FOREX"]
        )
        fresh_limit = thresholds["fresh_limit_ms"]
        stale_limit = thresholds["stale_limit_ms"]

        if age_ms <= fresh_limit:
            status = FreshnessStatus.FRESH
            reason = "DATA_FRESH_WITHIN_TOLERANCE"
            is_actionable = True
        elif age_ms <= stale_limit:
            status = FreshnessStatus.STALE
            reason = f"DATA_STALE (age {round(age_ms)}ms > limit {round(fresh_limit)}ms)"
            is_actionable = False
        else:
            status = FreshnessStatus.EXPIRED
            reason = f"DATA_EXPIRED (age {round(age_ms)}ms > max {round(stale_limit)}ms)"
            is_actionable = False

        return FreshnessResult(
            status=status,
            source_timestamp=src_iso,
            received_timestamp=rec_iso,
            data_age_ms=age_ms,
            data_age_seconds=age_sec,
            max_tolerated_age_ms=fresh_limit,
            reason=reason,
            is_actionable=is_actionable,
        )

    @classmethod
    def evaluate_candle_freshness(
        cls,
        candle_timestamp: Optional[datetime],
        timeframe: str,
        reference_time: Optional[datetime] = None,
    ) -> FreshnessResult:
        """
        Evaluates whether historical/recent candle data is fresh enough for technical evaluation.
        """
        now = reference_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        now_iso = now.isoformat()

        if candle_timestamp is None:
            return FreshnessResult(
                status=FreshnessStatus.UNAVAILABLE,
                source_timestamp="UNKNOWN",
                received_timestamp=now_iso,
                data_age_ms=-1.0,
                data_age_seconds=-1.0,
                max_tolerated_age_ms=600000.0,
                reason="MISSING_CANDLE_TIMESTAMP",
                is_actionable=False,
            )

        cand_time = candle_timestamp
        if cand_time.tzinfo is None:
            cand_time = cand_time.replace(tzinfo=timezone.utc)

        cand_iso = cand_time.isoformat()
        age_sec = (now - cand_time).total_seconds()
        age_ms = age_sec * 1000.0

        tf_key = timeframe.upper().replace("M", "M").replace("H", "H").replace("D", "D")
        tf_thresh = CANDLE_FRESHNESS_THRESHOLDS_SEC.get(
            tf_key, {"fresh_limit_sec": 7200.0, "stale_limit_sec": 14400.0}
        )

        fresh_sec = tf_thresh["fresh_limit_sec"]
        stale_sec = tf_thresh["stale_limit_sec"]

        if age_sec <= fresh_sec:
            status = FreshnessStatus.FRESH
            reason = "CANDLE_FRESH_WITHIN_WINDOW"
            is_actionable = True
        elif age_sec <= stale_sec:
            status = FreshnessStatus.STALE
            reason = f"CANDLE_STALE (age {round(age_sec)}s > window {round(fresh_sec)}s)"
            is_actionable = False
        else:
            status = FreshnessStatus.EXPIRED
            reason = f"CANDLE_EXPIRED (age {round(age_sec)}s > max {round(stale_sec)}s)"
            is_actionable = False

        return FreshnessResult(
            status=status,
            source_timestamp=cand_iso,
            received_timestamp=now_iso,
            data_age_ms=age_ms,
            data_age_seconds=age_sec,
            max_tolerated_age_ms=fresh_sec * 1000.0,
            reason=reason,
            is_actionable=is_actionable,
        )


freshness_service = DataFreshnessService()
