from typing import Any

import numpy as np
import pandas as pd


class MarketRegimeEngine:
    """
    Phase 5: Market Regime Engine
    Automatically classifies the current market state.
    """
    def __init__(self, atr_period: int = 14, adx_period: int = 14, sma_fast: int = 20, sma_slow: int = 50):
        self.atr_period = atr_period
        self.adx_period = adx_period
        self.sma_fast = sma_fast
        self.sma_slow = sma_slow

    def _calculate_tr(self, df: pd.DataFrame) -> pd.Series:
        high = df['high']
        low = df['low']
        close_prev = df['close'].shift(1)
        
        tr1 = high - low
        tr2 = (high - close_prev).abs()
        tr3 = (low - close_prev).abs()
        
        return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    def _calculate_adx(self, df: pd.DataFrame) -> pd.Series:
        if len(df) < self.adx_period + 1:
            return pd.Series(0, index=df.index)
            
        high = df['high']
        low = df['low']
        
        plus_dm = high.diff()
        minus_dm = low.diff()
        
        plus_dm = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0.0)
        minus_dm = np.where((minus_dm > plus_dm) & (minus_dm > 0), minus_dm.abs(), 0.0)
        
        tr = self._calculate_tr(df)
        atr = tr.rolling(self.adx_period).mean()
        
        plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(self.adx_period).mean() / atr)
        minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(self.adx_period).mean() / atr)
        
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        adx = dx.rolling(self.adx_period).mean()
        return adx.fillna(0)

    def analyze(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        Detects regimes: Trending, Strong Trend, Weak Trend, Range, Breakout, Pullback, Reversal, High/Low Volatility
        """
        if len(df) < self.sma_slow + 1:
            return {"trend": "UNKNOWN", "volatility": "NORMAL", "adx": 0.0, "state": "UNKNOWN"}
            
        # Volatility
        tr = self._calculate_tr(df)
        atr = tr.rolling(self.atr_period).mean()
        avg_atr = atr.mean()
        current_atr = atr.iloc[-1]
        
        volatility = "HIGH" if current_atr > (avg_atr * 1.5) else ("LOW" if current_atr < (avg_atr * 0.5) else "NORMAL")
        compression = "YES" if current_atr < (avg_atr * 0.3) else "NO"
        expansion = "YES" if current_atr > (avg_atr * 2.0) else "NO"
        
        # Trend
        adx = self._calculate_adx(df)
        current_adx = adx.iloc[-1]
        
        close = df['close']
        fast_sma = close.rolling(self.sma_fast).mean()
        slow_sma = close.rolling(self.sma_slow).mean()
        
        current_close = close.iloc[-1]
        fast = fast_sma.iloc[-1]
        slow = slow_sma.iloc[-1]
        
        trend = "RANGE"
        if current_adx > 25:
            if fast > slow:
                trend = "STRONG_BULLISH" if current_adx > 40 else "BULLISH"
            elif fast < slow:
                trend = "STRONG_BEARISH" if current_adx > 40 else "BEARISH"
        elif current_adx < 20:
            trend = "RANGE"
            
        # Breakout / Pullback logic
        state = "NEUTRAL"
        if trend in ["BULLISH", "STRONG_BULLISH"]:
            if current_close < fast and current_close > slow:
                state = "PULLBACK"
            elif current_close > df['high'].rolling(20).max().shift(1).iloc[-1]:
                state = "BREAKOUT"
        elif trend in ["BEARISH", "STRONG_BEARISH"]:
            if current_close > fast and current_close < slow:
                state = "PULLBACK"
            elif current_close < df['low'].rolling(20).min().shift(1).iloc[-1]:
                state = "BREAKOUT"
                
        # Reversal detection (Counter-trend extreme move)
        if (trend in ["BULLISH", "STRONG_BULLISH"] and current_close < slow and current_adx < 25):
            state = "REVERSAL_BEARISH"
        elif (trend in ["BEARISH", "STRONG_BEARISH"] and current_close > slow and current_adx < 25):
            state = "REVERSAL_BULLISH"

        return {
            "trend": trend,
            "state": state,
            "volatility": volatility,
            "compression": compression,
            "expansion": expansion,
            "adx": round(float(current_adx), 2),
            "atr": round(float(current_atr), 4)
        }

market_regime_engine = MarketRegimeEngine()
