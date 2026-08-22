"""
app/core/candle_discipline.py  — Phase 33
==========================================
CandleDisciplineChecker: Enforces that features used for signal generation
were computed using ONLY data available at prediction_timestamp.
No row in the DataFrame may have a timestamp >= prediction_timestamp.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

from app.logs.logger import get_logger

logger = get_logger(__name__)


class CandleDisciplineViolation(Exception):
    """Raised when look-ahead bias is detected in the input DataFrame."""
    pass


class CandleDisciplineResult:
    def __init__(
        self,
        passed: bool,
        prediction_timestamp: datetime,
        latest_candle_timestamp: datetime | None,
        violating_rows: int,
        previous_closed_candle_ts: datetime | None,
        current_candle_ts: datetime | None,
        next_candle_ts: datetime | None,
        reason: str | None = None,
    ):
        self.passed = passed
        self.prediction_timestamp = prediction_timestamp
        self.latest_candle_timestamp = latest_candle_timestamp
        self.violating_rows = violating_rows
        self.previous_closed_candle_ts = previous_closed_candle_ts
        self.current_candle_ts = current_candle_ts
        self.next_candle_ts = next_candle_ts
        self.reason = reason

    def to_dict(self) -> dict:
        def _iso(dt: datetime | None) -> str | None:
            return dt.isoformat() if dt else None

        return {
            "passed": self.passed,
            "prediction_timestamp": _iso(self.prediction_timestamp),
            "latest_candle_timestamp": _iso(self.latest_candle_timestamp),
            "violating_rows": self.violating_rows,
            "previous_closed_candle_ts": _iso(self.previous_closed_candle_ts),
            "current_candle_ts": _iso(self.current_candle_ts),
            "next_candle_ts": _iso(self.next_candle_ts),
            "reason": self.reason,
        }


class CandleDisciplineChecker:
    """
    Phase 33 candle look-ahead bias prevention.

    The strict rule:
        All candle timestamps in df must be STRICTLY LESS THAN prediction_timestamp.

    Violations indicate that a candle which has not yet closed was used in
    feature generation — a form of look-ahead bias.
    """

    @staticmethod
    def validate(
        df: pd.DataFrame,
        prediction_timestamp: datetime,
        raise_on_violation: bool = False,
    ) -> CandleDisciplineResult:
        """
        Validates that no row in df has a timestamp >= prediction_timestamp.

        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame. Timestamp may be the index or a 'timestamp' column.
        prediction_timestamp : datetime
            Exact moment the signal was generated. Must have tzinfo.
        raise_on_violation : bool
            If True, raises CandleDisciplineViolation on failure.
        """
        if prediction_timestamp.tzinfo is None:
            prediction_timestamp = prediction_timestamp.replace(tzinfo=timezone.utc)

        if df.empty:
            return CandleDisciplineResult(
                passed=False,
                prediction_timestamp=prediction_timestamp,
                latest_candle_timestamp=None,
                violating_rows=0,
                previous_closed_candle_ts=None,
                current_candle_ts=None,
                next_candle_ts=None,
                reason="EMPTY_DATAFRAME",
            )

        # Extract timestamps
        if isinstance(df.index, pd.DatetimeIndex):
            ts_series = df.index.to_series()
        elif "timestamp" in df.columns:
            ts_series = pd.to_datetime(df["timestamp"], utc=True)
        else:
            return CandleDisciplineResult(
                passed=False,
                prediction_timestamp=prediction_timestamp,
                latest_candle_timestamp=None,
                violating_rows=0,
                previous_closed_candle_ts=None,
                current_candle_ts=None,
                next_candle_ts=None,
                reason="NO_TIMESTAMP_COLUMN_OR_INDEX",
            )

        ts_series = pd.to_datetime(ts_series, utc=True)
        pred_ts_pd = pd.Timestamp(prediction_timestamp)

        # Strict less-than check
        violating = ts_series[ts_series >= pred_ts_pd]
        violating_count = len(violating)

        sorted_ts = ts_series.sort_values()
        latest_ts = sorted_ts.iloc[-1].to_pydatetime() if len(sorted_ts) > 0 else None

        # Closed candle = last row strictly before prediction_timestamp
        closed = ts_series[ts_series < pred_ts_pd]
        prev_closed = closed.iloc[-1].to_pydatetime() if len(closed) > 0 else None

        if violating_count > 0:
            reason = (
                f"LOOK_AHEAD_DETECTED: {violating_count} rows with ts >= "
                f"prediction_timestamp ({prediction_timestamp.isoformat()})"
            )
            logger.error(reason)
            if raise_on_violation:
                raise CandleDisciplineViolation(reason)

            return CandleDisciplineResult(
                passed=False,
                prediction_timestamp=prediction_timestamp,
                latest_candle_timestamp=latest_ts,
                violating_rows=violating_count,
                previous_closed_candle_ts=prev_closed,
                current_candle_ts=None,
                next_candle_ts=None,
                reason=reason,
            )

        logger.debug(
            f"Candle discipline PASSED — {len(df)} rows all before "
            f"{prediction_timestamp.isoformat()}"
        )
        return CandleDisciplineResult(
            passed=True,
            prediction_timestamp=prediction_timestamp,
            latest_candle_timestamp=latest_ts,
            violating_rows=0,
            previous_closed_candle_ts=prev_closed,
            current_candle_ts=None,
            next_candle_ts=None,
            reason=None,
        )
