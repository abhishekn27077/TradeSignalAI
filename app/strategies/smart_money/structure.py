from typing import Any

import pandas as pd

from app.logs.logger import get_logger

logger = get_logger(__name__)

class SMCStructureEngine:
    """
    Advanced Market Structure Engine detecting Internal and External Structure.
    Detects HH, HL, LH, LL, BOS, and CHoCH.
    """
    def __init__(self, external_lookback=20, internal_lookback=5):
        self.ext_lookback = external_lookback
        self.int_lookback = internal_lookback

    def detect_pivots(self, df: pd.DataFrame, window: int) -> tuple:
        """Find fractal swing highs and lows"""
        highs = df['high']
        lows = df['low']
        
        swing_highs = []
        swing_lows = []
        
        for i in range(window, len(df) - window):
            is_high = True
            is_low = True
            for j in range(1, window + 1):
                if highs.iloc[i] <= highs.iloc[i - j] or highs.iloc[i] <= highs.iloc[i + j]:
                    is_high = False
                if lows.iloc[i] >= lows.iloc[i - j] or lows.iloc[i] >= lows.iloc[i + j]:
                    is_low = False
            
            if is_high:
                swing_highs.append({"index": i, "price": highs.iloc[i], "timestamp": df.index[i]})
            if is_low:
                swing_lows.append({"index": i, "price": lows.iloc[i], "timestamp": df.index[i]})
                
        return swing_highs, swing_lows

    def label_structure(self, highs: list[dict], lows: list[dict]) -> list[dict]:
        """Label structure as HH, HL, LH, LL"""
        structure = []
        all_points = sorted(highs + lows, key=lambda x: x["index"])
        
        last_high = None
        last_low = None
        
        for point in all_points:
            is_high = any(p["index"] == point["index"] for p in highs)
            if is_high:
                if last_high is None:
                    point["type"] = "HH"
                else:
                    point["type"] = "HH" if point["price"] > last_high["price"] else "LH"
                last_high = point
            else:
                if last_low is None:
                    point["type"] = "LL"
                else:
                    point["type"] = "HL" if point["price"] > last_low["price"] else "LL"
                last_low = point
                
            structure.append(point)
            
        return structure

    def analyze(self, df: pd.DataFrame) -> dict[str, Any]:
        if len(df) < max(self.ext_lookback, self.int_lookback) * 2 + 1:
            return {"trend": "SIDEWAYS", "bos": False, "choch": False}

        # Detect External Structure
        ext_highs, ext_lows = self.detect_pivots(df, self.ext_lookback)
        ext_structure = self.label_structure(ext_highs, ext_lows)

        # Detect Internal Structure
        int_highs, int_lows = self.detect_pivots(df, self.int_lookback)
        int_structure = self.label_structure(int_highs, int_lows)

        trend = "SIDEWAYS"
        bos = False
        choch = False
        last_ext = ext_structure[-1] if ext_structure else None
        prev_ext = ext_structure[-2] if len(ext_structure) > 1 else None

        if last_ext and prev_ext:
            if last_ext["type"] in ["HH", "HL"]:
                trend = "BULLISH"
                if last_ext["type"] == "HH": bos = True
                if last_ext["type"] == "HL" and prev_ext["type"] in ["LH", "LL"]: choch = True
            elif last_ext["type"] in ["LH", "LL"]:
                trend = "BEARISH"
                if last_ext["type"] == "LL": bos = True
                if last_ext["type"] == "LH" and prev_ext["type"] in ["HH", "HL"]: choch = True

        return {
            "trend": trend,
            "bos": bos,
            "choch": choch,
            "external_structure": ext_structure,
            "internal_structure": int_structure
        }

market_structure = SMCStructureEngine()