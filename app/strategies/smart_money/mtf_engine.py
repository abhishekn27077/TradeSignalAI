from typing import Any

import pandas as pd

from app.logs.logger import get_logger
from app.strategies.smart_money.structure import market_structure

logger = get_logger(__name__)

class MultiTimeframeEngine:
    """
    MTF Engine to validate alignment across Daily, H4, H1, M15.
    Workflow: Daily -> Primary Trend, H4 -> Confirmation, H1 -> Structure, M15 -> Entry.
    """
    def __init__(self):
        pass

    def analyze(self, data_dict: dict[str, pd.DataFrame]) -> dict[str, Any]:
        """
        Accepts a dictionary of DataFrames keyed by timeframe: '1D', '4H', '1H', '15m'.
        Returns alignment status.
        """
        results = {}
        alignment = "CONFLICT"
        overall_trend = "SIDEWAYS"
        
        # Analyze each timeframe
        for tf in ["1D", "4H", "1H", "15m"]:
            if tf in data_dict and not data_dict[tf].empty:
                results[tf] = market_structure.analyze(data_dict[tf])
            else:
                results[tf] = {"trend": "SIDEWAYS"}
                
        daily_trend = results["1D"].get("trend", "SIDEWAYS")
        h4_trend = results["4H"].get("trend", "SIDEWAYS")
        h1_trend = results["1H"].get("trend", "SIDEWAYS")
        m15_trend = results["15m"].get("trend", "SIDEWAYS")
        
        if daily_trend == "BULLISH" and h4_trend == "BULLISH" and h1_trend == "BULLISH":
            alignment = "BULLISH_ALIGNED"
            overall_trend = "BULLISH"
        elif daily_trend == "BEARISH" and h4_trend == "BEARISH" and h1_trend == "BEARISH":
            alignment = "BEARISH_ALIGNED"
            overall_trend = "BEARISH"
            
        return {
            "alignment_status": alignment,
            "overall_trend": overall_trend,
            "timeframe_details": results,
            "is_tradable": alignment in ["BULLISH_ALIGNED", "BEARISH_ALIGNED"]
        }

mtf_engine = MultiTimeframeEngine()
