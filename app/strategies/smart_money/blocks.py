from typing import Any

import pandas as pd

from app.logs.logger import get_logger

logger = get_logger(__name__)

class SMCOrderBlockEngine:
    """
    Advanced Order Block Engine for SMC.
    Detects Bullish OB, Bearish OB, Breaker Blocks, Mitigated/Invalidated state, and assigns probability.
    """
    def __init__(self, atr_multiplier=1.5):
        self.atr_multiplier = atr_multiplier

    def analyze(self, df: pd.DataFrame) -> dict[str, Any]:
        if len(df) < 10:
            return {"bullish_obs": [], "bearish_obs": [], "breaker_blocks": []}
            
        bullish_obs = []
        bearish_obs = []
        breaker_blocks = []
        
        # Simple OB detection:
        # Bullish OB: Last down candle before a strong impulsive up move (BOS)
        # Bearish OB: Last up candle before a strong impulsive down move (BOS)
        
        for i in range(1, len(df) - 3):
            # Check for strong bullish impulse
            if df['close'].iloc[i+1] > df['open'].iloc[i+1] and df['close'].iloc[i+2] > df['open'].iloc[i+2]:
                # If i is a down candle
                if df['close'].iloc[i] < df['open'].iloc[i]:
                    bullish_obs.append({
                        "top_price": df['high'].iloc[i],
                        "bottom_price": df['low'].iloc[i],
                        "probability": 85.0, # Will be adjusted based on structure proximity
                        "mitigated": False,
                        "invalidated": False,
                        "index": i
                    })
                    
            # Check for strong bearish impulse
            if df['close'].iloc[i+1] < df['open'].iloc[i+1] and df['close'].iloc[i+2] < df['open'].iloc[i+2]:
                # If i is an up candle
                if df['close'].iloc[i] > df['open'].iloc[i]:
                    bearish_obs.append({
                        "top_price": df['high'].iloc[i],
                        "bottom_price": df['low'].iloc[i],
                        "probability": 85.0,
                        "mitigated": False,
                        "invalidated": False,
                        "index": i
                    })
                    
        # Check Mitigation
        recent_price = df['close'].iloc[-1]
        for ob in bullish_obs:
            if recent_price < ob["bottom_price"]:
                ob["invalidated"] = True
                breaker_blocks.append(ob) # Becomes a bearish breaker
            elif recent_price <= ob["top_price"]:
                ob["mitigated"] = True
                
        for ob in bearish_obs:
            if recent_price > ob["top_price"]:
                ob["invalidated"] = True
                breaker_blocks.append(ob) # Becomes a bullish breaker
            elif recent_price >= ob["bottom_price"]:
                ob["mitigated"] = True
                
        return {
            "bullish_obs": [ob for ob in bullish_obs if not ob["invalidated"]],
            "bearish_obs": [ob for ob in bearish_obs if not ob["invalidated"]],
            "breaker_blocks": breaker_blocks
        }

ob_engine = SMCOrderBlockEngine()