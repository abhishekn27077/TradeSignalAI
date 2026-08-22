import pandas as pd
import numpy as np
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timezone

from app.core.market_clock import MarketClockService
from app.strategies.Structure.models import (
    SwingPoint, SwingType, StructureType, Direction, StructureEvent
)
from app.strategies.Structure.swing import SwingDetector


class BOSEngine:
    """
    Break of Structure (BOS) Engine.
    Detects trend continuation breaks where price closes beyond recent swing high/low in direction of current bias.
    """

    def __init__(self, swing_len: int = 5):
        self.swing_detector = SwingDetector(left_len=swing_len, right_len=swing_len)

    def detect_bos(self, df: pd.DataFrame, asset: str = "UNKNOWN", timeframe: str = "1H") -> List[StructureEvent]:
        if df is None or len(df) < 15:
            return []

        swings = self.swing_detector.detect_swings(df, asset=asset, timeframe=timeframe)
        if len(swings) < 2:
            return []

        events: List[StructureEvent] = []
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        ts_col = 'timestamp' if 'timestamp' in df.columns else ('date' if 'date' in df.columns else None)

        # Track active swing points
        last_swing_high: Optional[SwingPoint] = None
        last_swing_low: Optional[SwingPoint] = None
        current_trend = Direction.NEUTRAL

        # Iterate through candles after initial swings
        for i in range(len(df)):
            # Update available confirmed swings up to candle i
            available_swings = [s for s in swings if (s.index + self.swing_detector.right_len) <= i]
            if not available_swings:
                continue

            # Identify latest high and low
            high_swings = [s for s in available_swings if s.swing_type == SwingType.SWING_HIGH]
            low_swings = [s for s in available_swings if s.swing_type == SwingType.SWING_LOW]

            latest_high = high_swings[-1] if high_swings else None
            latest_low = low_swings[-1] if low_swings else None

            curr_close = closes[i]

            # Detect Bullish BOS: Price closes above previous swing high
            if latest_high and curr_close > latest_high.price:
                # Check if this candle is the first one closing above this specific swing high
                if i > 0 and closes[i - 1] <= latest_high.price:
                    ts_raw = df.iloc[i][ts_col] if ts_col else datetime.now(timezone.utc)
                    ts_utc = self.swing_detector._parse_to_utc(ts_raw)
                    ts_ist = MarketClockService.format_ist(ts_utc)
                    
                    # Invalidation is the lowest low between swing high and current bar
                    inv_price = latest_low.price if latest_low else float(min(lows[latest_high.index:i+1]))
                    strength = min(1.0, max(0.1, (curr_close - latest_high.price) / (latest_high.price * 0.005 + 1e-6)))

                    events.append(StructureEvent(
                        asset=asset,
                        timeframe=timeframe,
                        event_type=StructureType.BULLISH_BOS,
                        direction=Direction.BULLISH,
                        price=float(curr_close),
                        timestamp_utc=ts_utc,
                        timestamp_ist=ts_ist,
                        source_candle=latest_high.index,
                        confirmation_candle=i,
                        strength=float(strength),
                        invalidation_price=float(inv_price),
                        details={"broken_swing_price": latest_high.price, "broken_swing_index": latest_high.index}
                    ))

            # Detect Bearish BOS: Price closes below previous swing low
            if latest_low and curr_close < latest_low.price:
                if i > 0 and closes[i - 1] >= latest_low.price:
                    ts_raw = df.iloc[i][ts_col] if ts_col else datetime.now(timezone.utc)
                    ts_utc = self.swing_detector._parse_to_utc(ts_raw)
                    ts_ist = MarketClockService.format_ist(ts_utc)

                    inv_price = latest_high.price if latest_high else float(max(highs[latest_low.index:i+1]))
                    strength = min(1.0, max(0.1, (latest_low.price - curr_close) / (latest_low.price * 0.005 + 1e-6)))

                    events.append(StructureEvent(
                        asset=asset,
                        timeframe=timeframe,
                        event_type=StructureType.BEARISH_BOS,
                        direction=Direction.BEARISH,
                        price=float(curr_close),
                        timestamp_utc=ts_utc,
                        timestamp_ist=ts_ist,
                        source_candle=latest_low.index,
                        confirmation_candle=i,
                        strength=float(strength),
                        invalidation_price=float(inv_price),
                        details={"broken_swing_price": latest_low.price, "broken_swing_index": latest_low.index}
                    ))

        return events


class CHoCHEngine:
    """
    Change of Character (CHoCH) Engine.
    Detects structural trend reversals when price violates the opposing structural pivot.
    """

    def __init__(self, swing_len: int = 5):
        self.swing_detector = SwingDetector(left_len=swing_len, right_len=swing_len)

    def detect_choch(self, df: pd.DataFrame, asset: str = "UNKNOWN", timeframe: str = "1H") -> List[StructureEvent]:
        if df is None or len(df) < 20:
            return []

        swings = self.swing_detector.detect_swings(df, asset=asset, timeframe=timeframe)
        if len(swings) < 3:
            return []

        events: List[StructureEvent] = []
        closes = df['close'].values
        ts_col = 'timestamp' if 'timestamp' in df.columns else ('date' if 'date' in df.columns else None)

        # Track trend state
        current_trend = Direction.NEUTRAL
        prev_trend = Direction.NEUTRAL

        for i in range(len(df)):
            available_swings = [s for s in swings if (s.index + self.swing_detector.right_len) <= i]
            if len(available_swings) < 3:
                continue

            high_swings = [s for s in available_swings if s.swing_type == SwingType.SWING_HIGH]
            low_swings = [s for s in available_swings if s.swing_type == SwingType.SWING_LOW]

            if len(high_swings) < 2 or len(low_swings) < 2:
                continue

            # Determine dominant recent trend prior to candle i
            if high_swings[-1].price > high_swings[-2].price and low_swings[-1].price > low_swings[-2].price:
                current_trend = Direction.BULLISH
            elif high_swings[-1].price < high_swings[-2].price and low_swings[-1].price < low_swings[-2].price:
                current_trend = Direction.BEARISH

            curr_close = closes[i]

            # Bullish CHoCH: In a Bearish trend, price closes above latest Lower High
            if current_trend == Direction.BEARISH and high_swings:
                recent_lh = high_swings[-1]
                if curr_close > recent_lh.price and (i > 0 and closes[i - 1] <= recent_lh.price):
                    ts_raw = df.iloc[i][ts_col] if ts_col else datetime.now(timezone.utc)
                    ts_utc = self.swing_detector._parse_to_utc(ts_raw)
                    ts_ist = MarketClockService.format_ist(ts_utc)

                    events.append(StructureEvent(
                        asset=asset,
                        timeframe=timeframe,
                        event_type=StructureType.BULLISH_CHOCH,
                        direction=Direction.BULLISH,
                        price=float(curr_close),
                        timestamp_utc=ts_utc,
                        timestamp_ist=ts_ist,
                        source_candle=recent_lh.index,
                        confirmation_candle=i,
                        strength=0.85,
                        invalidation_price=float(low_swings[-1].price if low_swings else curr_close * 0.99),
                        details={"reversal_from": "BEARISH", "broken_lh": recent_lh.price}
                    ))
                    current_trend = Direction.BULLISH

            # Bearish CHoCH: In a Bullish trend, price closes below latest Higher Low
            elif current_trend == Direction.BULLISH and low_swings:
                recent_hl = low_swings[-1]
                if curr_close < recent_hl.price and (i > 0 and closes[i - 1] >= recent_hl.price):
                    ts_raw = df.iloc[i][ts_col] if ts_col else datetime.now(timezone.utc)
                    ts_utc = self.swing_detector._parse_to_utc(ts_raw)
                    ts_ist = MarketClockService.format_ist(ts_utc)

                    events.append(StructureEvent(
                        asset=asset,
                        timeframe=timeframe,
                        event_type=StructureType.BEARISH_CHOCH,
                        direction=Direction.BEARISH,
                        price=float(curr_close),
                        timestamp_utc=ts_utc,
                        timestamp_ist=ts_ist,
                        source_candle=recent_hl.index,
                        confirmation_candle=i,
                        strength=0.85,
                        invalidation_price=float(high_swings[-1].price if high_swings else curr_close * 1.01),
                        details={"reversal_from": "BULLISH", "broken_hl": recent_hl.price}
                    ))
                    current_trend = Direction.BEARISH

        return events
