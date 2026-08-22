import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from app.core.market_clock import MarketClockService
from app.strategies.Structure.models import (
    SwingPoint, SwingType, StructureType, Direction, StructureEvent
)
from app.strategies.Structure.swing import SwingDetector


class MSBEngine:
    """
    Market Structure Break (MSB) Engine.
    Detects significant high-volume market structure breaks exceeding average range.
    """

    def __init__(self, swing_len: int = 5, vol_multiplier: float = 1.2):
        self.swing_detector = SwingDetector(left_len=swing_len, right_len=swing_len)
        self.vol_multiplier = vol_multiplier

    def detect_msb(self, df: pd.DataFrame, asset: str = "UNKNOWN", timeframe: str = "1H") -> List[StructureEvent]:
        if df is None or len(df) < 20:
            return []

        swings = self.swing_detector.detect_swings(df, asset=asset, timeframe=timeframe)
        if not swings:
            return []

        events: List[StructureEvent] = []
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        volumes = df['volume'].values if 'volume' in df.columns else np.ones(len(df))
        avg_vol = pd.Series(volumes).rolling(window=20, min_periods=1).mean().values
        ts_col = 'timestamp' if 'timestamp' in df.columns else ('date' if 'date' in df.columns else None)

        for i in range(len(df)):
            available_swings = [s for s in swings if (s.index + self.swing_detector.right_len) <= i]
            if not available_swings:
                continue

            curr_close = closes[i]
            curr_vol = volumes[i]
            vol_confirmed = curr_vol >= (avg_vol[i] * self.vol_multiplier) if avg_vol[i] > 0 else True

            high_swings = [s for s in available_swings if s.swing_type == SwingType.SWING_HIGH]
            low_swings = [s for s in available_swings if s.swing_type == SwingType.SWING_LOW]

            latest_high = high_swings[-1] if high_swings else None
            latest_low = low_swings[-1] if low_swings else None

            # Bullish MSB
            if latest_high and curr_close > latest_high.price and (i > 0 and closes[i - 1] <= latest_high.price):
                ts_raw = df.iloc[i][ts_col] if ts_col else datetime.now(timezone.utc)
                ts_utc = self.swing_detector._parse_to_utc(ts_raw)
                ts_ist = MarketClockService.format_ist(ts_utc)

                events.append(StructureEvent(
                    asset=asset,
                    timeframe=timeframe,
                    event_type=StructureType.BULLISH_MSB,
                    direction=Direction.BULLISH,
                    price=float(curr_close),
                    timestamp_utc=ts_utc,
                    timestamp_ist=ts_ist,
                    source_candle=latest_high.index,
                    confirmation_candle=i,
                    strength=0.9 if vol_confirmed else 0.7,
                    invalidation_price=float(latest_low.price if latest_low else curr_close * 0.98),
                    details={"volume_confirmed": bool(vol_confirmed), "broken_high": latest_high.price}
                ))

            # Bearish MSB
            if latest_low and curr_close < latest_low.price and (i > 0 and closes[i - 1] >= latest_low.price):
                ts_raw = df.iloc[i][ts_col] if ts_col else datetime.now(timezone.utc)
                ts_utc = self.swing_detector._parse_to_utc(ts_raw)
                ts_ist = MarketClockService.format_ist(ts_utc)

                events.append(StructureEvent(
                    asset=asset,
                    timeframe=timeframe,
                    event_type=StructureType.BEARISH_MSB,
                    direction=Direction.BEARISH,
                    price=float(curr_close),
                    timestamp_utc=ts_utc,
                    timestamp_ist=ts_ist,
                    source_candle=latest_low.index,
                    confirmation_candle=i,
                    strength=0.9 if vol_confirmed else 0.7,
                    invalidation_price=float(latest_high.price if latest_high else curr_close * 1.02),
                    details={"volume_confirmed": bool(vol_confirmed), "broken_low": latest_low.price}
                ))

        return events
