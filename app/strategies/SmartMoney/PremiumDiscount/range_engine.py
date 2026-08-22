import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from app.core.market_clock import MarketClockService
from app.strategies.Structure.models import SwingPoint, SwingType
from app.strategies.Structure.swing import SwingDetector


class ZoneType(str, Enum):
    PREMIUM = "PREMIUM"
    DISCOUNT = "DISCOUNT"
    EQUILIBRIUM = "EQUILIBRIUM"


@dataclass
class DealingRange:
    asset: str
    timeframe: str
    range_high: float
    range_low: float
    equilibrium_50: float
    ote_level: float       # Optimal Trade Entry (0.705 / 0.618)
    current_price: float
    zone: ZoneType
    premium_discount_pct: float  # 0.0 (extreme discount) to 1.0 (extreme premium)
    timestamp_utc: datetime
    timestamp_ist: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "timeframe": self.timeframe,
            "range_high": float(self.range_high),
            "range_low": float(self.range_low),
            "equilibrium_50": float(self.equilibrium_50),
            "ote_level": float(self.ote_level),
            "current_price": float(self.current_price),
            "zone": self.zone.value if hasattr(self.zone, 'value') else str(self.zone),
            "premium_discount_pct": float(self.premium_discount_pct),
            "timestamp_utc": self.timestamp_utc.isoformat() if isinstance(self.timestamp_utc, datetime) else str(self.timestamp_utc),
            "timestamp_ist": self.timestamp_ist,
            "details": self.details,
        }


class PremiumDiscountEngine:
    """
    Active Dealing Range & Premium / Discount Zone Engine.
    Uses confirmed structural swing extremes to evaluate equilibrium and institutional discount/premium zones.
    """

    def __init__(self, swing_len: int = 5):
        self.swing_detector = SwingDetector(left_len=swing_len, right_len=swing_len)

    def evaluate_range(self, df: pd.DataFrame, asset: str = "UNKNOWN", timeframe: str = "1H") -> DealingRange:
        now_utc = MarketClockService.get_current_utc()
        now_ist = MarketClockService.format_ist(now_utc)

        if df is None or len(df) < 10:
            return DealingRange(
                asset=asset,
                timeframe=timeframe,
                range_high=1.0,
                range_low=0.0,
                equilibrium_50=0.5,
                ote_level=0.7,
                current_price=0.5,
                zone=ZoneType.EQUILIBRIUM,
                premium_discount_pct=0.5,
                timestamp_utc=now_utc,
                timestamp_ist=now_ist
            )

        current_price = float(df['close'].iloc[-1])
        swings = self.swing_detector.detect_swings(df, asset=asset, timeframe=timeframe)

        if swings:
            high_swings = [s for s in swings if s.swing_type == SwingType.SWING_HIGH]
            low_swings = [s for s in swings if s.swing_type == SwingType.SWING_LOW]
            range_high = float(high_swings[-1].price) if high_swings else float(df['high'].max())
            range_low = float(low_swings[-1].price) if low_swings else float(df['low'].min())
        else:
            # Fallback to rolling window extremes
            range_high = float(df['high'].tail(50).max())
            range_low = float(df['low'].tail(50).min())

        if range_high <= range_low:
            range_high = current_price * 1.01
            range_low = current_price * 0.99

        range_span = range_high - range_low
        equilibrium = (range_high + range_low) / 2.0

        # Optimal Trade Entry (OTE) is 0.705 retrace level
        pct = (current_price - range_low) / (range_span + 1e-8)
        pct = max(0.0, min(1.0, pct))

        if pct > 0.52:
            zone = ZoneType.PREMIUM
            ote = range_low + (range_span * 0.705)
        elif pct < 0.48:
            zone = ZoneType.DISCOUNT
            ote = range_low + (range_span * 0.295)
        else:
            zone = ZoneType.EQUILIBRIUM
            ote = equilibrium

        return DealingRange(
            asset=asset,
            timeframe=timeframe,
            range_high=range_high,
            range_low=range_low,
            equilibrium_50=equilibrium,
            ote_level=ote,
            current_price=current_price,
            zone=zone,
            premium_discount_pct=pct,
            timestamp_utc=now_utc,
            timestamp_ist=now_ist,
            details={
                "fib_levels": {
                    "0.0": range_low,
                    "0.50": equilibrium,
                    "0.618": range_low + (range_span * 0.618),
                    "0.705": range_low + (range_span * 0.705),
                    "0.786": range_low + (range_span * 0.786),
                    "1.0": range_high
                }
            }
        )
