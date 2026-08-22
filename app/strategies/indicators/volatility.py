from typing import Any

import pandas as pd

from app.logs.logger import get_logger

logger = get_logger(__name__)

class ATRVolatilityEngine:
    """
    Computes ATR for dynamic Stop Loss, Take Profit, and trailing stops.
    Rejects low volatility markets.
    """
    def __init__(self, period=14, min_atr_threshold=0.0001):
        self.period = period
        self.min_atr = min_atr_threshold

    def calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        high = df['high']
        low = df['low']
        close = df['close'].shift(1)

        tr1 = high - low
        tr2 = (high - close).abs()
        tr3 = (low - close).abs()

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=self.period).mean()
        return atr

    def analyze(self, df: pd.DataFrame) -> dict[str, Any]:
        if len(df) < self.period + 1:
            return {"atr": 0.0, "is_volatile": False, "dynamic_sl": 0.0, "dynamic_tp": 0.0}
            
        atr_series = self.calculate_atr(df)
        current_atr = atr_series.iloc[-1]
        
        return {
            "atr": current_atr,
            "is_volatile": current_atr >= self.min_atr,
            "dynamic_sl_distance": current_atr * 1.5, # 1.5x ATR for SL
            "dynamic_tp_distance": current_atr * 3.0  # 3.0x ATR for TP (2:1 RR)
        }

volatility_engine = ATRVolatilityEngine()