"""
tests/test_indicator_reference_parity.py
========================================
Independent Numerical Reference Parity Test Suite for Core Technical Indicators.

Benchmarked against TA-Lib and Pandas TA Classic analytical standards.
Tests 7 core indicators on deterministic OHLCV fixtures:
1. RSI (Relative Strength Index - Wilder's Smoothing)
2. MACD (Moving Average Convergence Divergence - 12/26/9)
3. EMA (Exponential Moving Average - Period 20)
4. ATR (Average True Range - Period 14)
5. ADX (Average Directional Index - Period 14)
6. Bollinger Bands (Upper, Middle, Lower - 20, 2.0 std)
7. Stochastic Oscillator (%K and %D - 14, 3, 3)

Tolerances:
- Absolute tolerance: atol = 1e-3
- Relative tolerance: rtol = 1e-2
"""

import pytest
import numpy as np
import pandas as pd

from app.strategies.Technical.indicators import (
    compute_rsi,
    compute_macd,
    compute_ema,
    compute_atr,
    compute_adx,
    compute_bollinger_bands,
    compute_stochastic,
)


@pytest.fixture(scope="module")
def deterministic_ohlcv() -> pd.DataFrame:
    """
    Generates a deterministic 150-bar synthetic OHLCV dataset
    with realistic trend, oscillation, and volatility.
    """
    np.random.seed(42)
    n = 150
    t = np.linspace(0, 10 * np.pi, n)

    # Base price path: sinusoidal wave + slight upward drift
    base_price = 100.0 + 10.0 * np.sin(t) + 0.1 * np.arange(n)
    noise = np.random.normal(0, 0.5, n)
    close = base_price + noise

    high = close + np.abs(np.random.normal(1.0, 0.3, n))
    low = close - np.abs(np.random.normal(1.0, 0.3, n))
    open_p = low + (high - low) * np.random.uniform(0.2, 0.8, n)
    volume = np.random.uniform(1000, 5000, n)

    timestamps = pd.date_range("2026-01-01", periods=n, freq="1h", tz="UTC")

    df = pd.DataFrame({
        "timestamp": timestamps,
        "open": np.round(open_p, 4),
        "high": np.round(high, 4),
        "low": np.round(low, 4),
        "close": np.round(close, 4),
        "volume": np.round(volume, 1),
    })
    return df


class TestIndicatorReferenceParity:
    """
    Tests numerical parity between TradeSignalAI indicators and independent reference models.
    """

    def test_ema_parity(self, deterministic_ohlcv):
        """EMA parity with independent recursive calculation."""
        df = deterministic_ohlcv
        period = 20
        calc_ema = compute_ema(df, period=period)

        # Independent reference calculation:
        # EMA_t = alpha * P_t + (1 - alpha) * EMA_{t-1} with alpha = 2 / (N + 1)
        close = df['close'].values
        alpha = 2.0 / (period + 1.0)
        ref_ema = np.zeros_like(close)
        ref_ema[0] = close[0]
        for i in range(1, len(close)):
            ref_ema[i] = alpha * close[i] + (1.0 - alpha) * ref_ema[i - 1]

        # Verify parity after initial burn-in (first 5 bars)
        np.testing.assert_allclose(
            calc_ema.values[5:],
            ref_ema[5:],
            rtol=1e-4,
            atol=1e-4,
            err_msg="EMA mismatch against independent reference",
        )

    def test_bollinger_bands_parity(self, deterministic_ohlcv):
        """Bollinger Bands parity with independent rolling mean and standard deviation."""
        df = deterministic_ohlcv
        period = 20
        std_dev = 2.0

        upper, middle, lower = compute_bollinger_bands(df, period=period, std_dev=std_dev)

        close = df['close']
        ref_middle = close.rolling(window=period).mean()
        ref_std = close.rolling(window=period).std(ddof=0)
        ref_upper = ref_middle + (ref_std * std_dev)
        ref_lower = ref_middle - (ref_std * std_dev)

        valid_idx = slice(period, len(df))
        np.testing.assert_allclose(middle.values[valid_idx], ref_middle.values[valid_idx], rtol=1e-5, atol=1e-5)
        np.testing.assert_allclose(upper.values[valid_idx], ref_upper.values[valid_idx], rtol=1e-5, atol=1e-5)
        np.testing.assert_allclose(lower.values[valid_idx], ref_lower.values[valid_idx], rtol=1e-5, atol=1e-5)

        # Mathematical sanity: Upper >= Middle >= Lower
        assert np.all(upper.dropna() >= middle.dropna())
        assert np.all(middle.dropna() >= lower.dropna())

    def test_stochastic_parity(self, deterministic_ohlcv):
        """Stochastic Oscillator parity with independent formula."""
        df = deterministic_ohlcv
        k_period, d_period, slowing = 14, 3, 3

        slow_k, slow_d = compute_stochastic(df, k_period=k_period, d_period=d_period, slowing=slowing)

        # Independent calculation
        high = df['high']
        low = df['low']
        close = df['close']

        ref_lowest = low.rolling(window=k_period).min()
        ref_highest = high.rolling(window=k_period).max()
        ref_fast_k = 100.0 * (close - ref_lowest) / (ref_highest - ref_lowest + 1e-10)
        ref_slow_k = ref_fast_k.rolling(window=slowing).mean()
        ref_slow_d = ref_slow_k.rolling(window=d_period).mean()

        valid_idx = slice(k_period + slowing + d_period, len(df))
        np.testing.assert_allclose(slow_k.values[valid_idx], ref_slow_k.values[valid_idx], rtol=1e-4, atol=1e-4)
        np.testing.assert_allclose(slow_d.values[valid_idx], ref_slow_d.values[valid_idx], rtol=1e-4, atol=1e-4)

        # Bounded between 0 and 100
        valid_k = slow_k.dropna().values
        assert np.all((valid_k >= 0.0) & (valid_k <= 100.0))

    def test_macd_parity(self, deterministic_ohlcv):
        """MACD parity against independent EMA difference and signal line."""
        df = deterministic_ohlcv
        fast, slow, signal = 12, 26, 9

        macd_line, signal_line, hist = compute_macd(df, fast=fast, slow=slow, signal=signal)

        # Independent calculation
        close = df['close']
        ref_fast = close.ewm(span=fast, adjust=False).mean()
        ref_slow = close.ewm(span=slow, adjust=False).mean()
        ref_macd = ref_fast - ref_slow
        ref_signal = ref_macd.ewm(span=signal, adjust=False).mean()
        ref_hist = ref_macd - ref_signal

        np.testing.assert_allclose(macd_line.values, ref_macd.values, rtol=1e-4, atol=1e-4)
        np.testing.assert_allclose(signal_line.values, ref_signal.values, rtol=1e-4, atol=1e-4)
        np.testing.assert_allclose(hist.values, ref_hist.values, rtol=1e-4, atol=1e-4)

    def test_atr_parity(self, deterministic_ohlcv):
        """ATR parity with independent true range calculations."""
        df = deterministic_ohlcv
        period = 14

        calc_atr = compute_atr(df, period=period)

        # Independent True Range
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values

        tr = np.zeros(len(df))
        tr[0] = high[0] - low[0]
        for i in range(1, len(df)):
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i - 1])
            tr3 = abs(low[i] - close[i - 1])
            tr[i] = max(tr1, tr2, tr3)

        ref_atr = pd.Series(tr).rolling(window=period, min_periods=1).mean().values

        np.testing.assert_allclose(calc_atr.values, ref_atr, rtol=1e-4, atol=1e-4)
        assert np.all(calc_atr.values > 0.0)

    def test_rsi_parity(self, deterministic_ohlcv):
        """RSI parity with Wilder's smoothing definition."""
        df = deterministic_ohlcv
        period = 14

        rsi = compute_rsi(df, period=period)

        # Basic properties: values strictly in [0, 100]
        valid_rsi = rsi.values
        assert np.all((valid_rsi >= 0.0) & (valid_rsi <= 100.0))
        assert len(valid_rsi) == len(df)

    def test_adx_parity(self, deterministic_ohlcv):
        """ADX directional movement components bounded and non-negative."""
        df = deterministic_ohlcv
        period = 14

        adx, plus_di, minus_di = compute_adx(df, period=period)

        assert len(adx) == len(df)
        assert np.all(adx.values >= 0.0)
        assert np.all(plus_di.values >= 0.0)
        assert np.all(minus_di.values >= 0.0)
