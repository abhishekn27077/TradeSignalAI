"""
app/core/data_freshness.py  — Phase 33
======================================
DataFreshnessChecker: validates that market data is recent enough to use for
signal generation. Enforces candle-close discipline by confirming the last
candle is fully closed before prediction_timestamp.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.timing import CandleClock, ISTConverter
from app.logs.logger import get_logger

logger = get_logger(__name__)

# Maximum data age (seconds) per timeframe before DATA_STALE is returned
MAX_DATA_AGE_SECONDS: dict[str, int] = {
    "M1":  120,
    "M5":  300,
    "M15": 600,
    "M30": 900,
    "H1":  300,    # 5 min tolerance for H1
    "H4":  600,    # 10 min tolerance for H4
    "D1":  3600,   # 1 hour tolerance for daily
    "W1":  7200,
}


class DataFreshnessResult:
    def __init__(
        self,
        status: str,
        data_age_seconds: float | None,
        latest_candle_ts: str | None,
        prediction_timestamp_utc: str,
        prediction_timestamp_ist: str,
        previous_closed_candle: dict | None,
        current_open_candle: dict | None,
        next_candle_open: dict | None,
        provider: str,
        timeframe: str,
        symbol: str,
        reason: str | None = None,
    ):
        self.status = status                                    # FRESH | DATA_STALE | UNAVAILABLE
        self.data_age_seconds = data_age_seconds
        self.latest_candle_ts = latest_candle_ts
        self.prediction_timestamp_utc = prediction_timestamp_utc
        self.prediction_timestamp_ist = prediction_timestamp_ist
        self.previous_closed_candle = previous_closed_candle
        self.current_open_candle = current_open_candle
        self.next_candle_open = next_candle_open
        self.provider = provider
        self.timeframe = timeframe
        self.symbol = symbol
        self.reason = reason

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "data_age_seconds": self.data_age_seconds,
            "latest_candle_ts": self.latest_candle_ts,
            "prediction_timestamp_utc": self.prediction_timestamp_utc,
            "prediction_timestamp_ist": self.prediction_timestamp_ist,
            "previous_closed_candle": self.previous_closed_candle,
            "current_open_candle": self.current_open_candle,
            "next_candle_open": self.next_candle_open,
            "provider": self.provider,
            "timeframe": self.timeframe,
            "symbol": self.symbol,
            "reason": self.reason,
        }


class DataFreshnessChecker:
    """
    Phase 33 Zero-Trust Data Freshness Validator.

    Usage:
        result = DataFreshnessChecker.check("BTCUSD", "H4", rates, provider="yfinance")
        if result.status != "FRESH":
            return SIGNAL_BLOCKED
    """

    @staticmethod
    def check(
        symbol: str,
        timeframe: str,
        rates: list[dict[str, Any]],
        provider: str = "UNKNOWN",
        reference_time: datetime | None = None,
    ) -> DataFreshnessResult:
        now = reference_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        now_utc_str = now.isoformat()
        now_ist_str = ISTConverter.to_ist_string(now)

        if not rates:
            return DataFreshnessResult(
                status="UNAVAILABLE",
                data_age_seconds=None,
                latest_candle_ts=None,
                prediction_timestamp_utc=now_utc_str,
                prediction_timestamp_ist=now_ist_str,
                previous_closed_candle=None,
                current_open_candle=None,
                next_candle_open=None,
                provider=provider,
                timeframe=timeframe,
                symbol=symbol,
                reason="EMPTY_RATES_RESPONSE",
            )

        # Extract latest candle timestamp
        latest = rates[-1]
        latest_ts_raw = latest.get("timestamp") or latest.get("time") or latest.get("datetime")
        if latest_ts_raw is None:
            return DataFreshnessResult(
                status="UNAVAILABLE",
                data_age_seconds=None,
                latest_candle_ts=None,
                prediction_timestamp_utc=now_utc_str,
                prediction_timestamp_ist=now_ist_str,
                previous_closed_candle=None,
                current_open_candle=None,
                next_candle_open=None,
                provider=provider,
                timeframe=timeframe,
                symbol=symbol,
                reason="MISSING_TIMESTAMP_IN_RATES",
            )

        from datetime import timezone as tz
        import pandas as pd

        latest_ts = pd.to_datetime(latest_ts_raw, utc=True).to_pydatetime()
        if latest_ts.tzinfo is None:
            latest_ts = latest_ts.replace(tzinfo=timezone.utc)

        data_age = (now - latest_ts).total_seconds()

        # Get candle clock info
        try:
            candle_status = CandleClock.get_candle_status(timeframe, reference_time=now)
        except Exception:
            candle_status = {}

        previous_closed_candle = {
            "open": candle_status.get("current_candle_open_utc"),
            "close": candle_status.get("current_candle_close_utc"),
            "open_ist": candle_status.get("current_candle_open_ist"),
            "close_ist": candle_status.get("current_candle_close_ist"),
        }
        next_candle = {
            "open": candle_status.get("next_candle_open_utc"),
            "open_ist": candle_status.get("next_candle_open_ist"),
        }

        max_age = MAX_DATA_AGE_SECONDS.get(timeframe.upper(), 600)
        if data_age > max_age:
            logger.warning(
                f"DATA_STALE: {symbol} {timeframe} latest candle is {data_age:.0f}s old "
                f"(threshold: {max_age}s)"
            )
            return DataFreshnessResult(
                status="DATA_STALE",
                data_age_seconds=round(data_age, 1),
                latest_candle_ts=latest_ts.isoformat(),
                prediction_timestamp_utc=now_utc_str,
                prediction_timestamp_ist=now_ist_str,
                previous_closed_candle=previous_closed_candle,
                current_open_candle=None,
                next_candle_open=next_candle,
                provider=provider,
                timeframe=timeframe,
                symbol=symbol,
                reason=f"DATA_AGE_{int(data_age)}s_EXCEEDS_{max_age}s_THRESHOLD",
            )

        logger.info(
            f"DATA_FRESH: {symbol} {timeframe} — age {data_age:.0f}s (threshold {max_age}s)"
        )
        return DataFreshnessResult(
            status="FRESH",
            data_age_seconds=round(data_age, 1),
            latest_candle_ts=latest_ts.isoformat(),
            prediction_timestamp_utc=now_utc_str,
            prediction_timestamp_ist=now_ist_str,
            previous_closed_candle=previous_closed_candle,
            current_open_candle=None,
            next_candle_open=next_candle,
            provider=provider,
            timeframe=timeframe,
            symbol=symbol,
        )
