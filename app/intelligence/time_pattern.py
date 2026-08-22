"""
app/intelligence/time_pattern.py  — Phase 33
=============================================
HistoricalTimePatternEngine: validates current trading time against real
historical performance statistics. Phase 33: full trace output, min 15 samples,
no fake 50% win rates.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any

from app.market_data.service import market_service
from app.logs.logger import get_logger

logger = get_logger(__name__)

# Phase 33: configurable minimum sample threshold
MIN_SAMPLE_COUNT = 15

# Status constants (zero-trust)
STATUS_VALID       = "VALID"
STATUS_INSUFFICIENT = "INSUFFICIENT_HISTORICAL_SAMPLE"
STATUS_UNAVAILABLE = "UNAVAILABLE"


class HistoricalTimePatternEngine:
    """
    Searches the historical database for observations matching the exact
    day-of-week and hour, calculating exact bullish/bearish win rates.

    Zero-Trust Rules:
    - Never show win_rate unless sample_count >= MIN_SAMPLE_COUNT
    - Never output 50% unless samples prove it
    - Always return INSUFFICIENT_HISTORICAL_SAMPLE when samples < threshold
    """

    _stats_cache: dict = {}

    @classmethod
    async def build_cache(cls, symbol: str, timeframe: str = "H1", count: int = 1500):
        rates = await market_service.get_rates(symbol, timeframe, count=count)
        if not rates or len(rates) < 100:
            logger.warning(f"Insufficient data for time pattern cache: {symbol} {timeframe}")
            return False

        df = pd.DataFrame(rates)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)

        # Forward return: 12 periods for H1, 3 periods for H4
        fwd_periods = 12 if timeframe == "H1" else 3
        df['forward_return'] = df['close'].shift(-fwd_periods) / df['close'] - 1
        df.dropna(inplace=True)

        df['hour'] = df.index.hour
        df['day_of_week'] = df.index.dayofweek

        # Group by day + hour, compute full stats
        def bullish_count(x):
            return int((x > 0).sum())

        def bearish_count(x):
            return int((x <= 0).sum())

        grouped = df.groupby(['day_of_week', 'hour'])['forward_return'].agg(
            count='count',
            mean='mean',
            median='median',
            win_rate=lambda x: float((x > 0).mean()),
            bullish_count=lambda x: int((x > 0).sum()),
            bearish_count=lambda x: int((x <= 0).sum()),
        ).reset_index()

        key = f"{symbol}_{timeframe}"
        cls._stats_cache[key] = grouped
        logger.info(f"Time pattern cache built for {key}: {len(grouped)} buckets")
        return True

    @classmethod
    def analyze(
        cls,
        asset: str,
        current_time: datetime = None,
        timeframe: str = "H1",
    ) -> Dict[str, Any]:
        """
        Phase 33: Returns full trace with explicit sample counts.
        Never fabricates win_rate when samples are insufficient.
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        # Convert to IST for display
        try:
            import zoneinfo
            IST = zoneinfo.ZoneInfo("Asia/Kolkata")
            current_time_ist = current_time.astimezone(IST)
        except Exception:
            current_time_ist = current_time

        day_name = current_time.strftime("%A")
        day = current_time.weekday()
        hour_utc = current_time.hour
        hour_ist = current_time_ist.hour
        hour_block_utc = f"{hour_utc:02d}:00-{hour_utc + 1:02d}:00 UTC"
        hour_block_ist = f"{hour_ist:02d}:00-{hour_ist + 1:02d}:00 IST"

        _base = {
            "asset": asset,
            "timeframe": timeframe,
            "day_of_week": day_name,
            "day_index": day,
            "hour_utc": hour_utc,
            "hour_IST": hour_ist,
            "time_window": hour_block_utc,
            "time_window_IST": hour_block_ist,
        }

        key = f"{asset}_{timeframe}"
        if key not in cls._stats_cache:
            return {
                **_base,
                "status": STATUS_UNAVAILABLE,
                "sample_count": 0,
                "bullish_count": 0,
                "bearish_count": 0,
                "win_rate": "UNAVAILABLE",
                "average_forward_return": "UNAVAILABLE",
                "median_forward_return": "UNAVAILABLE",
                "historical_direction": "UNAVAILABLE",
            }

        df_stats = cls._stats_cache[key]
        match = df_stats[
            (df_stats['day_of_week'] == day) & (df_stats['hour'] == hour_utc)
        ]

        if match.empty:
            return {
                **_base,
                "status": STATUS_INSUFFICIENT,
                "sample_count": 0,
                "bullish_count": 0,
                "bearish_count": 0,
                "win_rate": "UNAVAILABLE",
                "average_forward_return": "UNAVAILABLE",
                "median_forward_return": "UNAVAILABLE",
                "historical_direction": "UNAVAILABLE",
            }

        row = match.iloc[0]
        obs = int(row['count'])
        bullish = int(row.get('bullish_count', 0))
        bearish = int(row.get('bearish_count', 0))

        if obs < MIN_SAMPLE_COUNT:
            return {
                **_base,
                "status": STATUS_INSUFFICIENT,
                "sample_count": obs,
                "bullish_count": bullish,
                "bearish_count": bearish,
                "win_rate": "UNAVAILABLE",
                "average_forward_return": "UNAVAILABLE",
                "median_forward_return": "UNAVAILABLE",
                "historical_direction": "UNAVAILABLE",
                "min_required": MIN_SAMPLE_COUNT,
            }

        win_rate = float(row['win_rate'])
        avg_ret = float(row['mean'])
        med_ret = float(row['median'])
        historical_direction = "BULLISH" if avg_ret > 0 else "BEARISH"

        return {
            **_base,
            "status": STATUS_VALID,
            "sample_count": obs,
            "bullish_count": bullish,
            "bearish_count": bearish,
            "win_rate": round(win_rate, 4),
            "average_forward_return": round(avg_ret, 5),
            "median_forward_return": round(med_ret, 5),
            "historical_direction": historical_direction,
            "min_required": MIN_SAMPLE_COUNT,
        }
