import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.core.market_clock import MarketClockService
from app.strategies.Structure.models import SwingPoint, SwingType
from app.strategies.Structure.swing import SwingDetector


class LiquidityType(str, Enum):
    EQUAL_HIGHS = "EQH"
    EQUAL_LOWS = "EQL"
    BUY_SIDE = "BSL"
    SELL_SIDE = "SSL"
    PREVIOUS_DAY_HIGH = "PDH"
    PREVIOUS_DAY_LOW = "PDL"
    PREVIOUS_WEEK_HIGH = "PWH"
    PREVIOUS_WEEK_LOW = "PWL"
    PREVIOUS_MONTH_HIGH = "PMH"
    PREVIOUS_MONTH_LOW = "PML"


@dataclass
class LiquidityPool:
    id: str
    asset: str
    timeframe: str
    liquidity_type: LiquidityType
    price: float
    volume_weight: float
    created_at_utc: datetime
    created_at_ist: str
    is_swept: bool = False
    sweep_timestamp_utc: Optional[datetime] = None
    touch_count: int = 1
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "asset": self.asset,
            "timeframe": self.timeframe,
            "liquidity_type": self.liquidity_type.value if hasattr(self.liquidity_type, 'value') else str(self.liquidity_type),
            "price": float(self.price),
            "volume_weight": float(self.volume_weight),
            "created_at_utc": self.created_at_utc.isoformat() if isinstance(self.created_at_utc, datetime) else str(self.created_at_utc),
            "created_at_ist": self.created_at_ist,
            "is_swept": self.is_swept,
            "sweep_timestamp_utc": self.sweep_timestamp_utc.isoformat() if self.sweep_timestamp_utc else None,
            "touch_count": self.touch_count,
            "details": self.details,
        }


class LiquidityEngine:
    """
    Identifies institutional liquidity pools:
    - Equal Highs (EQH) and Equal Lows (EQL)
    - Buy-side (BSL) and Sell-side (SSL) major swing liquidity
    - Reference levels: PDH, PDL, PWH, PWL, PMH, PML
    """

    def __init__(self, tolerance_pct: float = 0.001, swing_len: int = 5):
        self.tolerance_pct = tolerance_pct
        self.swing_detector = SwingDetector(left_len=swing_len, right_len=swing_len)

    def find_liquidity_pools(self, df: pd.DataFrame, asset: str = "UNKNOWN", timeframe: str = "1H") -> List[LiquidityPool]:
        if df is None or len(df) < 20:
            return []

        pools: List[LiquidityPool] = []
        swings = self.swing_detector.detect_swings(df, asset=asset, timeframe=timeframe)

        # 1. Equal Highs & Equal Lows Clustering
        high_swings = [s for s in swings if s.swing_type == SwingType.SWING_HIGH]
        low_swings = [s for s in swings if s.swing_type == SwingType.SWING_LOW]

        # Check Equal Highs
        for i in range(len(high_swings)):
            for j in range(i + 1, len(high_swings)):
                p1, p2 = high_swings[i].price, high_swings[j].price
                if abs(p1 - p2) / p1 <= self.tolerance_pct:
                    avg_price = (p1 + p2) / 2.0
                    pool_id = f"EQH-{asset}-{high_swings[j].index}"
                    pools.append(LiquidityPool(
                        id=pool_id,
                        asset=asset,
                        timeframe=timeframe,
                        liquidity_type=LiquidityType.EQUAL_HIGHS,
                        price=float(avg_price),
                        volume_weight=1.5,
                        created_at_utc=high_swings[j].timestamp_utc,
                        created_at_ist=high_swings[j].timestamp_ist,
                        touch_count=2,
                        details={"indices": [high_swings[i].index, high_swings[j].index], "prices": [p1, p2]}
                    ))

        # Check Equal Lows
        for i in range(len(low_swings)):
            for j in range(i + 1, len(low_swings)):
                p1, p2 = low_swings[i].price, low_swings[j].price
                if abs(p1 - p2) / p1 <= self.tolerance_pct:
                    avg_price = (p1 + p2) / 2.0
                    pool_id = f"EQL-{asset}-{low_swings[j].index}"
                    pools.append(LiquidityPool(
                        id=pool_id,
                        asset=asset,
                        timeframe=timeframe,
                        liquidity_type=LiquidityType.EQUAL_LOWS,
                        price=float(avg_price),
                        volume_weight=1.5,
                        created_at_utc=low_swings[j].timestamp_utc,
                        created_at_ist=low_swings[j].timestamp_ist,
                        touch_count=2,
                        details={"indices": [low_swings[i].index, low_swings[j].index], "prices": [p1, p2]}
                    ))

        # 2. Reference Higher-Timeframe Levels (PDH/PDL from historical daily aggregates)
        ref_pools = self._calculate_reference_levels(df, asset=asset, timeframe=timeframe)
        pools.extend(ref_pools)

        return pools

    def _calculate_reference_levels(self, df: pd.DataFrame, asset: str, timeframe: str) -> List[LiquidityPool]:
        ref_pools: List[LiquidityPool] = []
        ts_col = 'timestamp' if 'timestamp' in df.columns else ('date' if 'date' in df.columns else None)
        if not ts_col:
            return ref_pools

        try:
            temp_df = df.copy()
            temp_df['dt'] = pd.to_datetime(temp_df[ts_col], utc=True)
            temp_df = temp_df.sort_values('dt')

            # Calculate daily high/low for previous day
            daily_groups = temp_df.groupby(temp_df['dt'].dt.date)
            unique_dates = list(daily_groups.groups.keys())

            if len(unique_dates) >= 2:
                prev_date = unique_dates[-2]
                prev_day_df = daily_groups.get_group(prev_date)
                pdh = float(prev_day_df['high'].max())
                pdl = float(prev_day_df['low'].min())

                latest_utc = temp_df['dt'].iloc[-1].to_pydatetime()
                latest_ist = MarketClockService.format_ist(latest_utc)

                ref_pools.append(LiquidityPool(
                    id=f"PDH-{asset}-{prev_date}",
                    asset=asset,
                    timeframe="1D",
                    liquidity_type=LiquidityType.PREVIOUS_DAY_HIGH,
                    price=pdh,
                    volume_weight=2.0,
                    created_at_utc=latest_utc,
                    created_at_ist=latest_ist,
                    details={"date": str(prev_date)}
                ))
                ref_pools.append(LiquidityPool(
                    id=f"PDL-{asset}-{prev_date}",
                    asset=asset,
                    timeframe="1D",
                    liquidity_type=LiquidityType.PREVIOUS_DAY_LOW,
                    price=pdl,
                    volume_weight=2.0,
                    created_at_utc=latest_utc,
                    created_at_ist=latest_ist,
                    details={"date": str(prev_date)}
                ))
        except Exception:
            pass

        return ref_pools
