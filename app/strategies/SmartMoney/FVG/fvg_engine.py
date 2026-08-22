import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.core.market_clock import MarketClockService
from app.strategies.Structure.models import Direction


class FVGStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FULLY_FILLED = "FULLY_FILLED"
    INVALIDATED = "INVALIDATED"


@dataclass
class FairValueGap:
    id: str
    asset: str
    timeframe: str
    direction: Direction
    gap_high: float
    gap_low: float
    gap_size: float
    atr_normalized_size: float
    source_candle_index: int
    created_at_utc: datetime
    created_at_ist: str
    fill_percentage: float = 0.0
    fully_filled: bool = False
    status: FVGStatus = FVGStatus.ACTIVE
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "asset": self.asset,
            "timeframe": self.timeframe,
            "direction": self.direction.value if hasattr(self.direction, 'value') else str(self.direction),
            "gap_high": float(self.gap_high),
            "gap_low": float(self.gap_low),
            "gap_size": float(self.gap_size),
            "atr_normalized_size": float(self.atr_normalized_size),
            "source_candle_index": self.source_candle_index,
            "created_at_utc": self.created_at_utc.isoformat() if isinstance(self.created_at_utc, datetime) else str(self.created_at_utc),
            "created_at_ist": self.created_at_ist,
            "fill_percentage": float(self.fill_percentage),
            "fully_filled": self.fully_filled,
            "status": self.status.value if hasattr(self.status, 'value') else str(self.status),
            "details": self.details,
        }


class FVGEngine:
    """
    Zero-Lookahead Fair Value Gap (FVG) / Imbalance Engine.
    Detects 3-candle price imbalances and tracks real-time fill mitigation.
    """

    def __init__(self, min_atr_multiple: float = 0.2):
        self.min_atr_multiple = min_atr_multiple

    def detect_fvgs(self, df: pd.DataFrame, asset: str = "UNKNOWN", timeframe: str = "1H") -> List[FairValueGap]:
        if df is None or len(df) < 5:
            return []

        fvgs: List[FairValueGap] = []
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        ts_col = 'timestamp' if 'timestamp' in df.columns else ('date' if 'date' in df.columns else None)

        # Approximate ATR
        tr = np.maximum(highs[1:] - lows[1:], np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1])))
        atr = pd.Series(tr).rolling(window=14, min_periods=1).mean().values
        atr = np.insert(atr, 0, atr[0] if len(atr) > 0 else 1.0)

        for i in range(2, len(df)):
            c0_high, c0_low = highs[i - 2], lows[i - 2]
            c2_high, c2_low = highs[i], lows[i]
            curr_atr = atr[i] if atr[i] > 0 else 1.0

            # 1. Bullish FVG: Low of candle i is strictly above High of candle i-2
            if c2_low > c0_high:
                gap_size = c2_low - c0_high
                norm_size = gap_size / curr_atr
                if norm_size >= self.min_atr_multiple:
                    ts_raw = df.iloc[i][ts_col] if ts_col else datetime.now(timezone.utc)
                    ts_utc = self._parse_to_utc(ts_raw)
                    ts_ist = MarketClockService.format_ist(ts_utc)

                    fvg_id = f"FVG-BULL-{asset}-{i}"
                    fvg = FairValueGap(
                        id=fvg_id,
                        asset=asset,
                        timeframe=timeframe,
                        direction=Direction.BULLISH,
                        gap_high=float(c2_low),
                        gap_low=float(c0_high),
                        gap_size=float(gap_size),
                        atr_normalized_size=float(norm_size),
                        source_candle_index=i,
                        created_at_utc=ts_utc,
                        created_at_ist=ts_ist,
                        status=FVVGStatus.ACTIVE if 'FVVGStatus' in locals() else FVGStatus.ACTIVE
                    )
                    fvgs.append(fvg)

            # 2. Bearish FVG: High of candle i is strictly below Low of candle i-2
            if c2_high < c0_low:
                gap_size = c0_low - c2_high
                norm_size = gap_size / curr_atr
                if norm_size >= self.min_atr_multiple:
                    ts_raw = df.iloc[i][ts_col] if ts_col else datetime.now(timezone.utc)
                    ts_utc = self._parse_to_utc(ts_raw)
                    ts_ist = MarketClockService.format_ist(ts_utc)

                    fvg_id = f"FVG-BEAR-{asset}-{i}"
                    fvg = FairValueGap(
                        id=fvg_id,
                        asset=asset,
                        timeframe=timeframe,
                        direction=Direction.BEARISH,
                        gap_high=float(c0_low),
                        gap_low=float(c2_high),
                        gap_size=float(gap_size),
                        atr_normalized_size=float(norm_size),
                        source_candle_index=i,
                        created_at_utc=ts_utc,
                        created_at_ist=ts_ist,
                        status=FVGStatus.ACTIVE
                    )
                    fvgs.append(fvg)

        # 3. Simulate mitigation / fill percentages
        self._update_fvg_mitigations(fvgs, df)

        return fvgs

    def _update_fvg_mitigations(self, fvgs: List[FairValueGap], df: pd.DataFrame):
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values

        for fvg in fvgs:
            start_idx = fvg.source_candle_index + 1
            for k in range(start_idx, len(df)):
                curr_high = highs[k]
                curr_low = lows[k]
                curr_close = closes[k]

                if fvg.direction == Direction.BULLISH:
                    # Invalidation: candle closes below gap_low
                    if curr_close < fvg.gap_low:
                        fvg.status = FVGStatus.INVALIDATED
                        fvg.fill_percentage = 100.0
                        fvg.fully_filled = True
                        break

                    # Price dips into bullish gap [gap_low, gap_high]
                    if curr_low < fvg.gap_high:
                        filled_dist = fvg.gap_high - curr_low
                        fill_pct = min(100.0, max(0.0, (filled_dist / fvg.gap_size) * 100.0))
                        fvg.fill_percentage = max(fvg.fill_percentage, fill_pct)

                        if fvg.fill_percentage >= 95.0:
                            fvg.fully_filled = True
                            fvg.status = FVGStatus.FULLY_FILLED
                        else:
                            fvg.status = FVGStatus.PARTIALLY_FILLED

                elif fvg.direction == Direction.BEARISH:
                    # Invalidation: candle closes above gap_high
                    if curr_close > fvg.gap_high:
                        fvg.status = FVGStatus.INVALIDATED
                        fvg.fill_percentage = 100.0
                        fvg.fully_filled = True
                        break

                    # Price rallies into bearish gap [gap_low, gap_high]
                    if curr_high > fvg.gap_low:
                        filled_dist = curr_high - fvg.gap_low
                        fill_pct = min(100.0, max(0.0, (filled_dist / fvg.gap_size) * 100.0))
                        fvg.fill_percentage = max(fvg.fill_percentage, fill_pct)

                        if fvg.fill_percentage >= 95.0:
                            fvg.fully_filled = True
                            fvg.status = FVGStatus.FULLY_FILLED
                        else:
                            fvg.status = FVGStatus.PARTIALLY_FILLED

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
