import logging

import numpy as np
import pandas as pd


class MarketRegimeDetector:
    """
    Detects the current market regime from the following categories:
    Trending, Strong Trending, Range, Breakout, Low Volatility, High Volatility, News Event, Holiday
    """
    def __init__(self):
        self.logger = logging.getLogger("MarketRegimeDetector")
        
        self.ALLOWED_STRATEGIES_BY_REGIME = {
            "Trending": ["Trend", "Momentum", "HigherTF", "Historical", "Swing"],
            "Strong Trending": ["Trend", "Momentum", "HigherTF", "Historical", "Swing"],
            "Range": ["Pattern", "Liquidity", "Historical", "Swing"],
            "Breakout": ["Momentum", "Liquidity", "HigherTF", "Historical"],
            "Low Volatility": ["Pattern", "Liquidity"],
            "High Volatility": ["Momentum", "Swing"],
            "News Event": ["Liquidity"],  # Mostly stay out
            "Holiday": ["Pattern"] # Low liquidity
        }

    def is_strategy_allowed(self, regime: str, strategy_name: str) -> bool:
        if strategy_name in ["Risk", "MarketRegime", "Kronos"]:
            return True 
            
        allowed = self.ALLOWED_STRATEGIES_BY_REGIME.get(regime, [])
        return strategy_name in allowed
        
    def detect_regime(self, df: pd.DataFrame) -> str:
        """
        Detects the current regime using provided DataFrame.
        """
        if self._is_holiday():
            return "Holiday"
        if self._is_news_event():
            return "News Event"

        if df.empty or len(df) < 50:
            self.logger.warning("Not enough data to detect regime. Defaulting to Range.")
            return "Range"

        return self._classify_from_dataframe(df)

    def _classify_from_dataframe(self, df: pd.DataFrame) -> str:
        # Standardize columns to lowercase
        df = df.rename(columns=str.lower)
        
        close = df["close"].values
        high = df["high"].values
        low = df["low"].values
        volume = df["volume"].values if "volume" in df.columns else np.zeros(len(df))

        # --- Volatility (ATR Ratio) ---
        atr_window = 14
        tr = np.maximum(high[1:] - low[1:], np.abs(high[1:] - close[:-1]))
        tr = np.maximum(tr, np.abs(low[1:] - close[:-1]))
        
        if len(tr) < atr_window * 2:
            return "Range"
            
        atr = pd.Series(tr).rolling(atr_window).mean().values
        current_atr = atr[-1]
        historical_atr = np.nanmean(atr)
        
        if historical_atr == 0:
            atr_ratio = 1.0
        else:
            atr_ratio = current_atr / historical_atr

        if atr_ratio > 1.6:
            return "High Volatility"
        if atr_ratio < 0.6:
            return "Low Volatility"

        # --- Breakout (Volume + Bollinger Band Expansion) ---
        std = pd.Series(close).rolling(20).std().values
        current_std = std[-1]
        mean_std = np.nanmean(std)
        
        recent_vol = np.mean(volume[-5:]) if len(volume) >= 5 else 0
        hist_vol = np.mean(volume)
        
        if (mean_std > 0 and current_std / mean_std > 1.5) and (hist_vol > 0 and recent_vol / hist_vol > 1.5):
            return "Breakout"

        # --- Trend Strength (ADX Proxy) ---
        sma20 = pd.Series(close).rolling(20).mean().values[-1]
        sma50 = pd.Series(close).rolling(50).mean().values[-1]
        
        if not np.isnan(sma20) and not np.isnan(sma50) and sma50 != 0:
            trend_strength = abs(sma20 - sma50) / sma50 * 100
        else:
            trend_strength = 0
            
        sma20_series = pd.Series(close).rolling(20).mean()
        if len(sma20_series) >= 5:
            sma20_slope = abs(sma20_series.iloc[-1] - sma20_series.iloc[-5]) / sma20_series.iloc[-5] * 100
        else:
            sma20_slope = 0

        if trend_strength > 0.2 or sma20_slope > 0.15:
            if trend_strength > 0.4 or sma20_slope > 0.3:
                return "Strong Trending"
            return "Trending"
            
        return "Range"

    def _is_holiday(self) -> bool:
        return False

    def _is_news_event(self) -> bool:
        return False
