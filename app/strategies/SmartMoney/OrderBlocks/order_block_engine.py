import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.core.market_clock import MarketClockService
from app.strategies.Structure.models import Direction
from app.strategies.Structure.bos_choch import BOSEngine


class BlockType(str, Enum):
    BULLISH_OB = "BULLISH_OB"
    BEARISH_OB = "BEARISH_OB"
    BULLISH_BREAKER = "BULLISH_BREAKER"
    BEARISH_BREAKER = "BEARISH_BREAKER"
    MITIGATION_BLOCK = "MITIGATION_BLOCK"


class BlockStatus(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    TOUCHED = "TOUCHED"
    PARTIALLY_MITIGATED = "PARTIALLY_MITIGATED"
    FULLY_MITIGATED = "FULLY_MITIGATED"
    INVALIDATED = "INVALIDATED"


@dataclass
class OrderBlock:
    id: str
    asset: str
    timeframe: str
    block_type: BlockType
    direction: Direction
    price_high: float
    price_low: float
    source_candle_index: int
    created_at_utc: datetime
    created_at_ist: str
    strength: float
    touch_count: int = 0
    mitigation_percentage: float = 0.0
    invalidation_price: float = 0.0
    status: BlockStatus = BlockStatus.ACTIVE
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "asset": self.asset,
            "timeframe": self.timeframe,
            "block_type": self.block_type.value if hasattr(self.block_type, 'value') else str(self.block_type),
            "direction": self.direction.value if hasattr(self.direction, 'value') else str(self.direction),
            "price_high": float(self.price_high),
            "price_low": float(self.price_low),
            "source_candle_index": self.source_candle_index,
            "created_at_utc": self.created_at_utc.isoformat() if isinstance(self.created_at_utc, datetime) else str(self.created_at_utc),
            "created_at_ist": self.created_at_ist,
            "strength": float(self.strength),
            "touch_count": self.touch_count,
            "mitigation_percentage": float(self.mitigation_percentage),
            "invalidation_price": float(self.invalidation_price),
            "status": self.status.value if hasattr(self.status, 'value') else str(self.status),
            "details": self.details,
        }


class OrderBlockEngine:
    """
    Zero-Lookahead Order Block Engine.
    Detects institutional order blocks on confirmed candle closes and tracks mitigation lifecycles.
    """

    def __init__(self, swing_len: int = 5, impulse_threshold_atr: float = 1.5):
        self.bos_engine = BOSEngine(swing_len=swing_len)
        self.impulse_threshold_atr = impulse_threshold_atr

    def detect_order_blocks(self, df: pd.DataFrame, asset: str = "UNKNOWN", timeframe: str = "1H") -> List[OrderBlock]:
        if df is None or len(df) < 20:
            return []

        order_blocks: List[OrderBlock] = []
        highs = df['high'].values
        lows = df['low'].values
        opens = df['open'].values
        closes = df['close'].values
        ts_col = 'timestamp' if 'timestamp' in df.columns else ('date' if 'date' in df.columns else None)

        # Approximate ATR for impulse quantification
        tr = np.maximum(highs[1:] - lows[1:], np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1])))
        atr = pd.Series(tr).rolling(window=14, min_periods=1).mean().values
        atr = np.insert(atr, 0, atr[0] if len(atr) > 0 else 1.0)

        # Detect BOS events
        bos_events = self.bos_engine.detect_bos(df, asset=asset, timeframe=timeframe)
        bos_indices = {e.confirmation_candle: e for e in bos_events}

        for i in range(2, len(df)):
            # 1. Bullish Order Block: Down candle prior to an upward impulse or bullish BOS
            is_down_candle = closes[i - 1] < opens[i - 1]
            strong_up_move = (closes[i] - opens[i]) > (atr[i] * self.impulse_threshold_atr) or (i in bos_indices and bos_indices[i].direction == Direction.BULLISH)

            if is_down_candle and strong_up_move:
                ob_candle_idx = i - 1
                ob_high = float(highs[ob_candle_idx])
                ob_low = float(lows[ob_candle_idx])

                ts_raw = df.iloc[ob_candle_idx][ts_col] if ts_col else datetime.now(timezone.utc)
                ts_utc = self.bos_engine.swing_detector._parse_to_utc(ts_raw)
                ts_ist = MarketClockService.format_ist(ts_utc)

                ob_id = f"OB-BULL-{asset}-{ob_candle_idx}"
                ob = OrderBlock(
                    id=ob_id,
                    asset=asset,
                    timeframe=timeframe,
                    block_type=BlockType.BULLISH_OB,
                    direction=Direction.BULLISH,
                    price_high=ob_high,
                    price_low=ob_low,
                    source_candle_index=ob_candle_idx,
                    created_at_utc=ts_utc,
                    created_at_ist=ts_ist,
                    strength=0.85,
                    invalidation_price=ob_low,
                    status=BlockStatus.ACTIVE
                )
                order_blocks.append(ob)

            # 2. Bearish Order Block: Up candle prior to a downward impulse or bearish BOS
            is_up_candle = closes[i - 1] > opens[i - 1]
            strong_down_move = (opens[i] - closes[i]) > (atr[i] * self.impulse_threshold_atr) or (i in bos_indices and bos_indices[i].direction == Direction.BEARISH)

            if is_up_candle and strong_down_move:
                ob_candle_idx = i - 1
                ob_high = float(highs[ob_candle_idx])
                ob_low = float(lows[ob_candle_idx])

                ts_raw = df.iloc[ob_candle_idx][ts_col] if ts_col else datetime.now(timezone.utc)
                ts_utc = self.bos_engine.swing_detector._parse_to_utc(ts_raw)
                ts_ist = MarketClockService.format_ist(ts_utc)

                ob_id = f"OB-BEAR-{asset}-{ob_candle_idx}"
                ob = OrderBlock(
                    id=ob_id,
                    asset=asset,
                    timeframe=timeframe,
                    block_type=BlockType.BEARISH_OB,
                    direction=Direction.BEARISH,
                    price_high=ob_high,
                    price_low=ob_low,
                    source_candle_index=ob_candle_idx,
                    created_at_utc=ts_utc,
                    created_at_ist=ts_ist,
                    strength=0.85,
                    invalidation_price=ob_high,
                    status=BlockStatus.ACTIVE
                )
                order_blocks.append(ob)

        # 3. Simulate Mitigation & Invalidation Lifecycle up to the latest candle
        self._update_order_block_lifecycles(order_blocks, df)

        return order_blocks

    def _update_order_block_lifecycles(self, order_blocks: List[OrderBlock], df: pd.DataFrame):
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values

        for ob in order_blocks:
            start_idx = ob.source_candle_index + 1
            for k in range(start_idx, len(df)):
                curr_high = highs[k]
                curr_low = lows[k]
                curr_close = closes[k]

                if ob.direction == Direction.BULLISH:
                    # Invalidation: price closes below OB low
                    if curr_close < ob.invalidation_price:
                        ob.status = BlockStatus.INVALIDATED
                        ob.details["is_breaker"] = True
                        break

                    # Touch / Mitigation: price enters OB range [price_low, price_high]
                    if curr_low <= ob.price_high:
                        ob.touch_count += 1
                        penetration = (ob.price_high - curr_low) / (ob.price_high - ob.price_low + 1e-6)
                        ob.mitigation_percentage = max(ob.mitigation_percentage, min(100.0, penetration * 100.0))

                        if ob.mitigation_percentage >= 90.0:
                            ob.status = BlockStatus.FULLY_MITIGATED
                        elif ob.mitigation_percentage >= 25.0:
                            ob.status = BlockStatus.PARTIALLY_MITIGATED
                        else:
                            ob.status = BlockStatus.TOUCHED

                elif ob.direction == Direction.BEARISH:
                    # Invalidation: price closes above OB high
                    if curr_close > ob.invalidation_price:
                        ob.status = BlockStatus.INVALIDATED
                        ob.details["is_breaker"] = True
                        break

                    # Touch / Mitigation: price enters OB range [price_low, price_high]
                    if curr_high >= ob.price_low:
                        ob.touch_count += 1
                        penetration = (curr_high - ob.price_low) / (ob.price_high - ob.price_low + 1e-6)
                        ob.mitigation_percentage = max(ob.mitigation_percentage, min(100.0, penetration * 100.0))

                        if ob.mitigation_percentage >= 90.0:
                            ob.status = BlockStatus.FULLY_MITIGATED
                        elif ob.mitigation_percentage >= 25.0:
                            ob.status = BlockStatus.PARTIALLY_MITIGATED
                        else:
                            ob.status = BlockStatus.TOUCHED
