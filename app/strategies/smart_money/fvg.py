from typing import Any

import pandas as pd

from app.logs.logger import get_logger

logger = get_logger(__name__)

class SMCFairValueGapEngine:
    """
    Advanced FVG Engine for SMC.
    Detects Bullish/Bearish FVGs, calculates gap size, strength, fill percentage, age, and mitigation.
    """
    def __init__(self, min_gap_size=0.0):
        self.min_gap_size = min_gap_size

    def analyze(self, df: pd.DataFrame) -> dict[str, Any]:
        if len(df) < 4:
            return {"bullish_fvgs": [], "bearish_fvgs": []}
            
        bullish_fvgs = []
        bearish_fvgs = []
        
        # FVG is a 3-candle pattern.
        # Bullish FVG: Low of candle 3 > High of candle 1
        # Bearish FVG: High of candle 3 < Low of candle 1
        
        for i in range(2, len(df)):
            c1_high = df['high'].iloc[i-2]
            c1_low = df['low'].iloc[i-2]
            c3_high = df['high'].iloc[i]
            c3_low = df['low'].iloc[i]
            
            # Bullish FVG
            if c3_low > c1_high:
                gap = c3_low - c1_high
                if gap > self.min_gap_size:
                    bullish_fvgs.append({
                        "top_price": c3_low,
                        "bottom_price": c1_high,
                        "gap_size": gap,
                        "gap_strength": gap / c1_high * 100, # Percentage gap
                        "fill_percentage": 0.0,
                        "age": len(df) - i,
                        "mitigated": False,
                        "index": i
                    })
                    
            # Bearish FVG
            if c3_high < c1_low:
                gap = c1_low - c3_high
                if gap > self.min_gap_size:
                    bearish_fvgs.append({
                        "top_price": c1_low,
                        "bottom_price": c3_high,
                        "gap_size": gap,
                        "gap_strength": gap / c3_high * 100,
                        "fill_percentage": 0.0,
                        "age": len(df) - i,
                        "mitigated": False,
                        "index": i
                    })
                    
        # Check Mitigation and Fill Percentage using subsequent price action
        for fvg in bullish_fvgs:
            subsequent_lows = df['low'].iloc[fvg["index"]+1:]
            if not subsequent_lows.empty:
                min_low = subsequent_lows.min()
                if min_low <= fvg["bottom_price"]:
                    fvg["mitigated"] = True
                    fvg["fill_percentage"] = 100.0
                elif min_low < fvg["top_price"]:
                    fill = (fvg["top_price"] - min_low) / fvg["gap_size"] * 100
                    fvg["fill_percentage"] = max(fvg["fill_percentage"], fill)
                    
        for fvg in bearish_fvgs:
            subsequent_highs = df['high'].iloc[fvg["index"]+1:]
            if not subsequent_highs.empty:
                max_high = subsequent_highs.max()
                if max_high >= fvg["top_price"]:
                    fvg["mitigated"] = True
                    fvg["fill_percentage"] = 100.0
                elif max_high > fvg["bottom_price"]:
                    fill = (max_high - fvg["bottom_price"]) / fvg["gap_size"] * 100
                    fvg["fill_percentage"] = max(fvg["fill_percentage"], fill)
                    
        return {
            "bullish_fvgs": bullish_fvgs,
            "bearish_fvgs": bearish_fvgs
        }

fvg_engine = SMCFairValueGapEngine()
