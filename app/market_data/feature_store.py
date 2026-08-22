from typing import Any

import numpy as np
import pandas as pd


class FeatureStore:
    """
    Calculates and stores technical indicators and market structure features.
    """
    
    def __init__(self):
        # In a real enterprise app, this would use Redis for fast lookups
        self._cache: dict[str, pd.DataFrame] = {}
        
    def calculate_features(self, symbol: str, timeframe: str, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all required features for a dataframe.
        """
        if df.empty:
            return df
            
        df = df.copy()
        
        # Trend Indicators
        df['EMA_9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['EMA_21'] = df['close'].ewm(span=21, adjust=False).mean()
        df['SMA_50'] = df['close'].rolling(window=50).mean()
        df['SMA_200'] = df['close'].rolling(window=200).mean()
        
        # Momentum Indicators
        df['RSI'] = self._calculate_rsi(df['close'], 14)
        df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = self._calculate_macd(df['close'])
        
        # Volatility
        df['ATR'] = self._calculate_atr(df, 14)
        df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = self._calculate_bollinger_bands(df['close'])
        
        # Market Structure (Simplified)
        df['Swing_High'] = df['high'] == df['high'].rolling(window=5, center=True).max()
        df['Swing_Low'] = df['low'] == df['low'].rolling(window=5, center=True).min()
        
        # Caching
        cache_key = f"{symbol}_{timeframe}"
        self._cache[cache_key] = df
        
        return df

    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
        
    def _calculate_macd(self, series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal, adjust=False).mean()
        macd_hist = macd - macd_signal
        return macd, macd_signal, macd_hist
        
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.rolling(period).mean()
        
    def _calculate_bollinger_bands(self, series: pd.Series, period: int = 20, std_dev: int = 2):
        middle = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
        
    def get_latest_features(self, symbol: str, timeframe: str) -> Optional[dict[str, Any]]:
        cache_key = f"{symbol}_{timeframe}"
        df = self._cache.get(cache_key)
        if df is None or df.empty:
            return None
        return df.iloc[-1].to_dict()
