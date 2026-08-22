import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.strategies.Structure.models import SwingPoint, SwingType, Direction
from app.strategies.Structure.swing import SwingDetector


class StructureStrengthEngine:
    """
    Evaluates market structure strength, trend persistence, and impulse dynamics.
    Outputs a normalized score (0-100) and discrete structural state.
    """

    def __init__(self, swing_len: int = 5):
        self.swing_detector = SwingDetector(left_len=swing_len, right_len=swing_len)

    def evaluate_strength(self, df: pd.DataFrame, asset: str = "UNKNOWN", timeframe: str = "1H") -> Dict[str, Any]:
        if df is None or len(df) < 20:
            return {
                "asset": asset,
                "timeframe": timeframe,
                "score": 50.0,
                "bias": "NEUTRAL",
                "state": "UNCERTAIN",
                "hh_count": 0,
                "hl_count": 0,
                "lh_count": 0,
                "ll_count": 0,
                "impulse_ratio": 1.0,
            }

        swings = self.swing_detector.detect_swings(df, asset=asset, timeframe=timeframe)
        high_swings = [s for s in swings if s.swing_type == SwingType.SWING_HIGH]
        low_swings = [s for s in swings if s.swing_type == SwingType.SWING_LOW]

        hh_count = 0
        lh_count = 0
        for i in range(1, len(high_swings)):
            if high_swings[i].price > high_swings[i - 1].price:
                hh_count += 1
            else:
                lh_count += 1

        hl_count = 0
        ll_count = 0
        for i in range(1, len(low_swings)):
            if low_swings[i].price > low_swings[i - 1].price:
                hl_count += 1
            else:
                ll_count += 1

        bullish_score = (hh_count * 15) + (hl_count * 15)
        bearish_score = (ll_count * 15) + (lh_count * 15)

        total_swings = len(high_swings) + len(low_swings)
        if total_swings == 0:
            score = 50.0
            bias = Direction.NEUTRAL
            state = "RANGE"
        else:
            diff = bullish_score - bearish_score
            score = max(0.0, min(100.0, 50.0 + diff))

            if score >= 75.0:
                bias = Direction.BULLISH
                state = "STRONG_BULLISH"
            elif score >= 60.0:
                bias = Direction.BULLISH
                state = "WEAK_BULLISH"
            elif score <= 25.0:
                bias = Direction.BEARISH
                state = "STRONG_BEARISH"
            elif score <= 40.0:
                bias = Direction.BEARISH
                state = "WEAK_BEARISH"
            else:
                bias = Direction.NEUTRAL
                state = "RANGE"

        return {
            "asset": asset,
            "timeframe": timeframe,
            "score": float(score),
            "bias": bias.value if hasattr(bias, 'value') else str(bias),
            "state": state,
            "hh_count": hh_count,
            "hl_count": hl_count,
            "lh_count": lh_count,
            "ll_count": ll_count,
            "swings_analyzed": len(swings),
        }
