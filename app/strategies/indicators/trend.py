from typing import Any

import pandas as pd

from app.logs.logger import get_logger

logger = get_logger(__name__)

class ADXTrendEngine:
    """
    Calculates ADX to determine trend strength.
    Rejects sideways markets (ADX < threshold).
    """
    def __init__(self, period=14, adx_threshold=25.0):
        self.period = period
        self.threshold = adx_threshold

    def calculate_adx(self, df: pd.DataFrame) -> pd.DataFrame:
        high = df['high']
        low = df['low']
        close = df['close'].shift(1)
        
        plus_dm = high.diff()
        minus_dm = low.diff()
        
        plus_dm[plus_dm < 0] = 0
        plus_dm[plus_dm < -minus_dm] = 0
        
        minus_dm = -minus_dm
        minus_dm[minus_dm < 0] = 0
        minus_dm[minus_dm < plus_dm] = 0
        
        tr1 = high - low
        tr2 = (high - close).abs()
        tr3 = (low - close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.ewm(alpha=1/self.period, adjust=False).mean()
        plus_di = 100 * (plus_dm.ewm(alpha=1/self.period, adjust=False).mean() / atr)
        minus_di = 100 * (minus_dm.ewm(alpha=1/self.period, adjust=False).mean() / atr)
        
        dx = (abs(plus_di - minus_di) / abs(plus_di + minus_di)) * 100
        adx = dx.ewm(alpha=1/self.period, adjust=False).mean()
        
        return pd.DataFrame({"+DI": plus_di, "-DI": minus_di, "ADX": adx})

    def analyze(self, df: pd.DataFrame) -> dict[str, Any]:
        if len(df) < self.period * 2:
            return {"adx": 0.0, "is_trending": False}
            
        adx_df = self.calculate_adx(df)
        current_adx = adx_df['ADX'].iloc[-1]
        
        return {
            "adx": current_adx,
            "plus_di": adx_df['+DI'].iloc[-1],
            "minus_di": adx_df['-DI'].iloc[-1],
            "is_trending": current_adx >= self.threshold
        }

trend_engine = ADXTrendEngine()