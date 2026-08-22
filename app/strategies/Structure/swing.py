import numpy as np
import pandas as pd
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from app.core.market_clock import MarketClockService
from app.strategies.Structure.models import SwingPoint, SwingType, Direction


class SwingDetector:
    """
    Deterministic Zero-Lookahead Swing Point Detector.
    A swing high at bar i is confirmed strictly at bar (i + right_len).
    No future data beyond bar (i + right_len) is referenced.
    """

    def __init__(self, left_len: int = 5, right_len: int = 5):
        self.left_len = max(1, left_len)
        self.right_len = max(1, right_len)

    def detect_swings(self, df: pd.DataFrame, asset: str = "UNKNOWN", timeframe: str = "1H") -> List[SwingPoint]:
        """
        Detects confirmed swing highs and lows in a chronological OHLCV DataFrame.
        Expected columns: ['timestamp' or 'date', 'open', 'high', 'low', 'close']
        """
        if df is None or len(df) < (self.left_len + self.right_len + 1):
            return []

        swings: List[SwingPoint] = []
        highs = df['high'].values
        lows = df['low'].values
        volumes = df['volume'].values if 'volume' in df.columns else np.zeros(len(df))

        # Resolve timestamp column
        ts_col = 'timestamp' if 'timestamp' in df.columns else ('date' if 'date' in df.columns else None)

        n = len(df)
        for i in range(self.left_len, n - self.right_len):
            # Check swing high
            curr_high = highs[i]
            is_swing_high = True
            for l in range(i - self.left_len, i):
                if highs[l] >= curr_high:
                    is_swing_high = False
                    break
            if is_swing_high:
                for r in range(i + 1, i + self.right_len + 1):
                    if highs[r] > curr_high:
                        is_swing_high = False
                        break

            if is_swing_high:
                # Timestamp of the swing bar
                ts_raw = df.iloc[i][ts_col] if ts_col else datetime.now(timezone.utc)
                ts_utc = self._parse_to_utc(ts_raw)
                ts_ist = MarketClockService.format_ist(ts_utc)
                swings.append(SwingPoint(
                    asset=asset,
                    timeframe=timeframe,
                    index=i,
                    timestamp_utc=ts_utc,
                    timestamp_ist=ts_ist,
                    price=float(curr_high),
                    swing_type=SwingType.SWING_HIGH,
                    confirmed=True,
                    volume=float(volumes[i])
                ))

            # Check swing low
            curr_low = lows[i]
            is_swing_low = True
            for l in range(i - self.left_len, i):
                if lows[l] <= curr_low:
                    is_swing_low = False
                    break
            if is_swing_low:
                for r in range(i + 1, i + self.right_len + 1):
                    if lows[r] < curr_low:
                        is_swing_low = False
                        break

            if is_swing_low:
                ts_raw = df.iloc[i][ts_col] if ts_col else datetime.now(timezone.utc)
                ts_utc = self._parse_to_utc(ts_raw)
                ts_ist = MarketClockService.format_ist(ts_utc)
                swings.append(SwingPoint(
                    asset=asset,
                    timeframe=timeframe,
                    index=i,
                    timestamp_utc=ts_utc,
                    timestamp_ist=ts_ist,
                    price=float(curr_low),
                    swing_type=SwingType.SWING_LOW,
                    confirmed=True,
                    volume=float(volumes[i])
                ))

        # Sort chronologically by index
        swings.sort(key=lambda s: s.index)
        return swings

    def _parse_to_utc(self, dt_val: Any) -> datetime:
        if isinstance(dt_val, datetime):
            if dt_val.tzinfo is None:
                return dt_val.replace(tzinfo=timezone.utc)
            return dt_val.astimezone(timezone.utc)
        if isinstance(dt_val, str):
            try:
                dt = datetime.fromisoformat(dt_val.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                pass
        return datetime.now(timezone.utc)


class InternalStructureDetector(SwingDetector):
    """Detects minor / internal sub-structure swings with smaller lookbacks."""
    def __init__(self, left_len: int = 3, right_len: int = 3):
        super().__init__(left_len=left_len, right_len=right_len)


class SwingStructureDetector(SwingDetector):
    """Detects major swing structure swings with larger lookbacks (e.g. 10/10)."""
    def __init__(self, left_len: int = 10, right_len: int = 10):
        super().__init__(left_len=left_len, right_len=right_len)
