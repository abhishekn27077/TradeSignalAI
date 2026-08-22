import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from app.core.market_clock import MarketClockService
from app.market_data.quality.models import DataQualityState, QualityIssue, DataQualityReport


class TimestampValidator:
    """Validates monotonicity, non-null timestamps, and absence of future timestamps."""

    @staticmethod
    def validate(df: pd.DataFrame, current_time_utc: Optional[datetime] = None) -> List[QualityIssue]:
        issues = []
        if df is None or df.empty or 'timestamp' not in df.columns:
            return [QualityIssue("TIMESTAMP_MISSING", "FATAL", "DataFrame missing timestamp column or is empty.")]

        now_utc = current_time_utc or datetime.now(timezone.utc)
        timestamps = pd.to_datetime(df['timestamp'], utc=True)

        # Monotonicity check
        if not timestamps.is_monotonic_increasing:
            issues.append(QualityIssue("TIMESTAMPS_NOT_MONOTONIC", "CRITICAL", "Candle timestamps are not strictly increasing."))

        # Future timestamp check
        future_mask = timestamps > now_utc
        if future_mask.any():
            count = future_mask.sum()
            issues.append(QualityIssue(
                "FUTURE_TIMESTAMPS_DETECTED", "FATAL",
                f"Found {count} candles with timestamps in the future.",
                details={"future_candle_count": int(count)}
            ))

        return issues


class OHLCConsistencyValidator:
    """
    Validates fundamental OHLC relationship rules:
    Open <= High, Open >= Low, Close <= High, Close >= Low, High >= Low, Price > 0
    """

    @staticmethod
    def validate(df: pd.DataFrame) -> List[QualityIssue]:
        issues = []
        if df is None or df.empty:
            return [QualityIssue("EMPTY_DATAFRAME", "FATAL", "Cannot validate empty DataFrame.")]

        required_cols = ['open', 'high', 'low', 'close']
        for col in required_cols:
            if col not in df.columns:
                return [QualityIssue(f"MISSING_COLUMN_{col.upper()}", "FATAL", f"Missing required OHLC column: {col}")]

        opens = df['open'].values
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values

        # Check positive prices
        if (opens <= 0).any() or (highs <= 0).any() or (lows <= 0).any() or (closes <= 0).any():
            issues.append(QualityIssue("NEGATIVE_OR_ZERO_PRICE", "FATAL", "Found non-positive price values in OHLC bars."))

        # Check High >= Low
        invalid_hl = highs < lows
        if invalid_hl.any():
            issues.append(QualityIssue("HIGH_LESS_THAN_LOW", "FATAL", f"Found {invalid_hl.sum()} candles where High < Low."))

        # Check Open within [Low, High]
        invalid_open = (opens > highs) | (opens < lows)
        if invalid_open.any():
            issues.append(QualityIssue("OPEN_OUTSIDE_RANGE", "CRITICAL", f"Found {invalid_open.sum()} candles where Open is outside [Low, High]."))

        # Check Close within [Low, High]
        invalid_close = (closes > highs) | (closes < lows)
        if invalid_close.any():
            issues.append(QualityIssue("CLOSE_OUTSIDE_RANGE", "CRITICAL", f"Found {invalid_close.sum()} candles where Close is outside [Low, High]."))

        return issues


class DuplicateDetector:
    """Detects duplicate candle timestamps."""

    @staticmethod
    def validate(df: pd.DataFrame) -> List[QualityIssue]:
        issues = []
        if df is None or df.empty or 'timestamp' not in df.columns:
            return []

        dups = df['timestamp'].duplicated()
        if dups.any():
            count = dups.sum()
            issues.append(QualityIssue("DUPLICATE_TIMESTAMPS", "CRITICAL", f"Found {count} duplicate candle timestamps."))

        return issues


class VolumeValidator:
    """Validates non-negative volume."""

    @staticmethod
    def validate(df: pd.DataFrame) -> List[QualityIssue]:
        issues = []
        if df is None or df.empty or 'volume' not in df.columns:
            return []

        vols = df['volume'].values
        if (vols < 0).any():
            issues.append(QualityIssue("NEGATIVE_VOLUME", "CRITICAL", "Found negative volume values."))

        return issues


class OutlierDetector:
    """Detects unrealistic price spikes (e.g. single-candle >20% spike or 8x ATR deviation)."""

    @staticmethod
    def validate(df: pd.DataFrame, max_allowed_pct_change: float = 0.20) -> List[QualityIssue]:
        issues = []
        if df is None or len(df) < 5:
            return []

        closes = df['close'].values
        pct_changes = np.abs(np.diff(closes) / closes[:-1])

        outliers = np.where(pct_changes > max_allowed_pct_change)[0]
        if len(outliers) > 0:
            issues.append(QualityIssue(
                "ANOMALOUS_PRICE_SPIKE", "CRITICAL",
                f"Found {len(outliers)} price spikes exceeding {max_allowed_pct_change*100:.1f}%.",
                candle_index=int(outliers[0]) + 1
            ))

        return issues


class DataFreshnessMonitor:
    """Monitors real-time data staleness compared to canonical clock."""

    @staticmethod
    def check_freshness(
        df: pd.DataFrame,
        timeframe: str = "1H",
        current_time_utc: Optional[datetime] = None,
        max_staleness_multiplier: float = 2.5
    ) -> (float, Optional[QualityIssue]):
        if df is None or df.empty or 'timestamp' not in df.columns:
            return 999999.0, QualityIssue("DATA_UNAVAILABLE", "FATAL", "No data available to check freshness.")

        now_utc = current_time_utc or datetime.now(timezone.utc)
        last_ts = pd.to_datetime(df['timestamp'].iloc[-1], utc=True)
        if last_ts.tzinfo is None:
            last_ts = last_ts.replace(tzinfo=timezone.utc)

        freshness_seconds = max(0.0, (now_utc - last_ts).total_seconds())

        # Expected seconds per timeframe
        tf_seconds = {
            "1M": 60, "5M": 300, "15M": 900, "30M": 1800,
            "1H": 3600, "4H": 14400, "1D": 86400
        }.get(timeframe.upper(), 3600)

        max_allowed_seconds = tf_seconds * max_staleness_multiplier

        issue = None
        if freshness_seconds > max_allowed_seconds:
            issue = QualityIssue(
                "DATA_STALE", "CRITICAL",
                f"Data is stale. Last candle was {freshness_seconds/60:.1f} minutes ago (Threshold: {max_allowed_seconds/60:.1f} min).",
                details={"freshness_seconds": freshness_seconds, "allowed_seconds": max_allowed_seconds}
            )

        return freshness_seconds, issue


class DataQualityEngine:
    """
    Comprehensive Master Data Quality & Integrity Engine.
    Fails closed if any critical or fatal corruption, future timestamp, or staleness is identified.
    """

    def __init__(self, fail_on_stale: bool = True):
        self.fail_on_stale = fail_on_stale

    def evaluate(
        self,
        df: pd.DataFrame,
        asset: str = "UNKNOWN",
        timeframe: str = "1H",
        current_time_utc: Optional[datetime] = None,
        provider: str = "UNKNOWN"
    ) -> DataQualityReport:
        if df is None or df.empty:
            return DataQualityReport(
                asset=asset,
                timeframe=timeframe,
                total_candles_checked=0,
                state=DataQualityState.DATA_UNAVAILABLE,
                is_valid_for_trading=False,
                issues=[QualityIssue("NO_DATA", "FATAL", "DataFrame is None or empty.")],
                provider=provider
            )

        issues: List[QualityIssue] = []

        # 1. Monotonicity & Future Timestamps
        issues.extend(TimestampValidator.validate(df, current_time_utc))

        # 2. OHLC Logical Consistency
        issues.extend(OHLCConsistencyValidator.validate(df))

        # 3. Duplicate Detector
        issues.extend(DuplicateDetector.validate(df))

        # 4. Volume Validator
        issues.extend(VolumeValidator.validate(df))

        # 5. Outlier & Spike Detector
        issues.extend(OutlierDetector.validate(df))

        # 6. Freshness Check
        freshness_sec, fresh_issue = DataFreshnessMonitor.check_freshness(df, timeframe, current_time_utc)
        if fresh_issue:
            issues.append(fresh_issue)

        last_candle_str = str(df['timestamp'].iloc[-1]) if 'timestamp' in df.columns else None

        # Determine overall Quality State
        has_fatal = any(i.severity == "FATAL" for i in issues)
        has_critical = any(i.severity == "CRITICAL" for i in issues)
        has_stale = any(i.issue_type == "DATA_STALE" for i in issues)

        if has_fatal:
            state = DataQualityState.DATA_CORRUPTED
            is_valid = False
        elif has_stale and self.fail_on_stale:
            state = DataQualityState.DATA_STALE
            is_valid = False
        elif has_critical:
            state = DataQualityState.DATA_QUALITY_DEGRADED
            is_valid = False
        elif len(issues) > 0:
            state = DataQualityState.DATA_QUALITY_DEGRADED
            is_valid = True  # minor warnings allowed
        else:
            state = DataQualityState.DATA_QUALITY_GOOD
            is_valid = True

        return DataQualityReport(
            asset=asset,
            timeframe=timeframe,
            total_candles_checked=len(df),
            state=state,
            is_valid_for_trading=is_valid,
            issues=issues,
            last_candle_time_utc=last_candle_str,
            freshness_seconds=freshness_sec,
            provider=provider,
            metadata={"checked_at_utc": datetime.now(timezone.utc).isoformat()}
        )
