import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, Optional


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Computes Average True Range (ATR)."""
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values

    tr1 = high[1:] - low[1:]
    tr2 = np.abs(high[1:] - close[:-1])
    tr3 = np.abs(low[1:] - close[:-1])
    tr = np.maximum(tr1, np.maximum(tr2, tr3))
    tr = np.insert(tr, 0, high[0] - low[0])

    atr_series = pd.Series(tr).rolling(window=period, min_periods=1).mean()
    return atr_series


def compute_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Computes Relative Strength Index (RSI)."""
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    # Wilder's smoothing
    for i in range(period, len(df)):
        avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period

    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def compute_adx(df: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Computes Average Directional Index (ADX), +DI, -DI."""
    high = df['high']
    low = df['low']
    close = df['close']

    tr = compute_atr(df, period=1)
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    tr_smooth = pd.Series(tr).rolling(window=period, min_periods=1).sum()
    plus_di = 100 * (pd.Series(plus_dm).rolling(window=period, min_periods=1).sum() / (tr_smooth + 1e-10))
    minus_di = 100 * (pd.Series(minus_dm).rolling(window=period, min_periods=1).sum() / (tr_smooth + 1e-10))

    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
    adx = dx.rolling(window=period, min_periods=1).mean().fillna(20.0)

    return adx, plus_di.fillna(0.0), minus_di.fillna(0.0)


def compute_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Computes MACD Line, Signal Line, and Histogram."""
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def compute_vwap(df: pd.DataFrame) -> pd.Series:
    """Computes Volume Weighted Average Price (VWAP)."""
    typical_price = (df['high'] + df['low'] + df['close']) / 3.0
    vol = df['volume'] if 'volume' in df.columns else pd.Series(np.ones(len(df)))
    vwap = (typical_price * vol).cumsum() / (vol.cumsum() + 1e-10)
    return vwap


def compute_ema(data: pd.DataFrame | pd.Series, period: int = 20) -> pd.Series:
    """Computes Exponential Moving Average (EMA)."""
    series = data['close'] if isinstance(data, pd.DataFrame) else data
    return series.ewm(span=period, adjust=False).mean()


def compute_bollinger_bands(
    data: pd.DataFrame | pd.Series,
    period: int = 20,
    std_dev: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Computes Bollinger Bands (Upper, Middle/SMA, Lower).
    Uses population or standard Bessel-corrected standard deviation.
    """
    series = data['close'] if isinstance(data, pd.DataFrame) else data
    middle = series.rolling(window=period, min_periods=period).mean()
    rolling_std = series.rolling(window=period, min_periods=period).std(ddof=0)
    upper = middle + (rolling_std * std_dev)
    lower = middle - (rolling_std * std_dev)
    return upper, middle, lower


def compute_stochastic(
    df: pd.DataFrame,
    k_period: int = 14,
    d_period: int = 3,
    slowing: int = 3
) -> Tuple[pd.Series, pd.Series]:
    """
    Computes Full Stochastic Oscillator (%K and %D).
    Fast %K = 100 * (Close - LowestLow) / (HighestHigh - LowestLow)
    Slow %K = SMA(Fast %K, slowing)
    %D = SMA(Slow %K, d_period)
    """
    high = df['high']
    low = df['low']
    close = df['close']

    lowest_low = low.rolling(window=k_period, min_periods=k_period).min()
    highest_high = high.rolling(window=k_period, min_periods=k_period).max()

    denom = highest_high - lowest_low + 1e-10
    fast_k = 100.0 * (close - lowest_low) / denom

    if slowing > 1:
        slow_k = fast_k.rolling(window=slowing, min_periods=slowing).mean()
    else:
        slow_k = fast_k

    slow_d = slow_k.rolling(window=d_period, min_periods=d_period).mean()
    return slow_k, slow_d

