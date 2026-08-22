import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.core.market_clock import MarketClockService
from app.strategies.Structure.models import Direction
from app.strategies.SmartMoney.Liquidity.liquidity_engine import (
    LiquidityEngine, LiquidityPool, LiquidityType
)


class SweepType(str, Enum):
    BULLISH_SWEEP = "BULLISH_SWEEP"  # Swept sell-side liquidity, closed higher
    BEARISH_SWEEP = "BEARISH_SWEEP"  # Swept buy-side liquidity, closed lower
    FAILED_SWEEP = "FAILED_SWEEP"    # Closed beyond liquidity pool (breakout, not sweep)


@dataclass
class SweepEvent:
    id: str
    asset: str
    timeframe: str
    sweep_type: SweepType
    direction: Direction
    liquidity_pool_id: str
    liquidity_price: float
    sweep_price: float
    close_price: float
    candle_index: int
    timestamp_utc: datetime
    timestamp_ist: str
    strength: float
    structural_confirmation: bool = False
    requires_confluence: bool = True  # Sweep alone cannot trade

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "asset": self.asset,
            "timeframe": self.timeframe,
            "sweep_type": self.sweep_type.value if hasattr(self.sweep_type, 'value') else str(self.sweep_type),
            "direction": self.direction.value if hasattr(self.direction, 'value') else str(self.direction),
            "liquidity_pool_id": self.liquidity_pool_id,
            "liquidity_price": float(self.liquidity_price),
            "sweep_price": float(self.sweep_price),
            "close_price": float(self.close_price),
            "candle_index": self.candle_index,
            "timestamp_utc": self.timestamp_utc.isoformat() if isinstance(self.timestamp_utc, datetime) else str(self.timestamp_utc),
            "timestamp_ist": self.timestamp_ist,
            "strength": float(self.strength),
            "structural_confirmation": self.structural_confirmation,
            "requires_confluence": self.requires_confluence,
        }


class LiquiditySweepDetector:
    """
    Detects Liquidity Sweeps where price takes out resting stop orders
    and immediately rejects back into the dealing range.
    """

    def __init__(self, tolerance_pct: float = 0.001):
        self.liquidity_engine = LiquidityEngine(tolerance_pct=tolerance_pct)

    def detect_sweeps(self, df: pd.DataFrame, asset: str = "UNKNOWN", timeframe: str = "1H") -> List[SweepEvent]:
        if df is None or len(df) < 10:
            return []

        pools = self.liquidity_engine.find_liquidity_pools(df, asset=asset, timeframe=timeframe)
        if not pools:
            return []

        sweeps: List[SweepEvent] = []
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        opens = df['open'].values
        ts_col = 'timestamp' if 'timestamp' in df.columns else ('date' if 'date' in df.columns else None)

        for pool in pools:
            level_price = pool.price

            # Search subsequent candles for sweeps
            for i in range(len(df)):
                curr_high = highs[i]
                curr_low = lows[i]
                curr_close = closes[i]

                # Check Bullish Sweep (Sell-side sweep: Low wicks below level, Close finishes ABOVE level)
                if pool.liquidity_type in [LiquidityType.EQUAL_LOWS, LiquidityType.SELL_SIDE, LiquidityType.PREVIOUS_DAY_LOW]:
                    if curr_low < level_price and curr_close > level_price:
                        ts_raw = df.iloc[i][ts_col] if ts_col else datetime.now(timezone.utc)
                        ts_utc = self.liquidity_engine.swing_detector._parse_to_utc(ts_raw)
                        ts_ist = MarketClockService.format_ist(ts_utc)

                        wick_penetration = (level_price - curr_low) / level_price
                        strength = min(1.0, max(0.2, wick_penetration * 500))

                        sweeps.append(SweepEvent(
                            id=f"SWEEP-BULL-{asset}-{i}",
                            asset=asset,
                            timeframe=timeframe,
                            sweep_type=SweepType.BULLISH_SWEEP,
                            direction=Direction.BULLISH,
                            liquidity_pool_id=pool.id,
                            liquidity_price=level_price,
                            sweep_price=float(curr_low),
                            close_price=float(curr_close),
                            candle_index=i,
                            timestamp_utc=ts_utc,
                            timestamp_ist=ts_ist,
                            strength=float(strength),
                            structural_confirmation=False,
                            requires_confluence=True
                        ))

                # Check Bearish Sweep (Buy-side sweep: High wicks above level, Close finishes BELOW level)
                if pool.liquidity_type in [LiquidityType.EQUAL_HIGHS, LiquidityType.BUY_SIDE, LiquidityType.PREVIOUS_DAY_HIGH]:
                    if curr_high > level_price and curr_close < level_price:
                        ts_raw = df.iloc[i][ts_col] if ts_col else datetime.now(timezone.utc)
                        ts_utc = self.liquidity_engine.swing_detector._parse_to_utc(ts_raw)
                        ts_ist = MarketClockService.format_ist(ts_utc)

                        wick_penetration = (curr_high - level_price) / level_price
                        strength = min(1.0, max(0.2, wick_penetration * 500))

                        sweeps.append(SweepEvent(
                            id=f"SWEEP-BEAR-{asset}-{i}",
                            asset=asset,
                            timeframe=timeframe,
                            sweep_type=SweepType.BEARISH_SWEEP,
                            direction=Direction.BEARISH,
                            liquidity_pool_id=pool.id,
                            liquidity_price=level_price,
                            sweep_price=float(curr_high),
                            close_price=float(curr_close),
                            candle_index=i,
                            timestamp_utc=ts_utc,
                            timestamp_ist=ts_ist,
                            strength=float(strength),
                            structural_confirmation=False,
                            requires_confluence=True
                        ))

        return sweeps
