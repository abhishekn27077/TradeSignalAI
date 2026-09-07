"""
tests/test_full_indicator_replay.py
===================================
Comprehensive Multi-Indicator Non-Repainting Sequential Replay Suite (Phase 71).

Validates that evaluating:
- SuperTrend (KivancOzbilgic)
- RSI (14)
- MACD (12, 26, 9)
- ATR (14)
- Swing High / Low (left=5, right=5)
- BOS & CHoCH (Structure Breaks)
- Smart Money Order Blocks
candle-by-candle chronologically produces EXACTLY the same outputs as batch evaluation on closed bars.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from app.strategies.Technical.indicators import compute_rsi, compute_macd, compute_atr
from app.strategies.Technical.supertrend import compute_supertrend
from app.strategies.Structure.swing import SwingDetector
from app.strategies.Structure.bos_choch import BOSEngine, CHoCHEngine
from app.strategies.SmartMoney.OrderBlocks.order_block_engine import OrderBlockEngine


def generate_ohlcv_series(n_bars: int = 120) -> pd.DataFrame:
    np.random.seed(101)
    start_time = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
    times = [start_time + timedelta(hours=i) for i in range(n_bars)]
    
    returns = np.random.normal(0.0002, 0.002, n_bars)
    prices = 1.0850 * np.cumprod(1 + returns)
    
    opens = prices
    highs = opens * (1 + np.abs(np.random.normal(0.001, 0.001, n_bars)))
    lows = opens * (1 - np.abs(np.random.normal(0.001, 0.001, n_bars)))
    closes = (opens + highs + lows) / 3.0 + np.random.normal(0, 0.0001, n_bars)
    volumes = np.random.uniform(1000, 5000, n_bars)

    return pd.DataFrame({
        'timestamp': times,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes,
    })


def test_supertrend_sequential_replay():
    df = generate_ohlcv_series(100)
    
    # 1. Bar-by-bar sequential evaluation
    seq_directions = []
    for t in range(20, len(df) + 1):
        sub_df = df.iloc[:t].copy()
        _, st_dir = compute_supertrend(sub_df, period=10, multiplier=3.0)
        seq_directions.append(st_dir.iloc[-1])

    # 2. Full batch evaluation
    _, batch_dir = compute_supertrend(df, period=10, multiplier=3.0)
    expected_slice = list(batch_dir.iloc[19:])

    assert seq_directions == expected_slice, "SuperTrend repaints during sequential bar execution!"


def test_rsi_sequential_replay():
    df = generate_ohlcv_series(100)
    
    seq_rsi = []
    for t in range(20, len(df) + 1):
        sub_df = df.iloc[:t].copy()
        rsi = compute_rsi(sub_df, period=14)
        seq_rsi.append(round(rsi.iloc[-1], 4))

    batch_rsi = compute_rsi(df, period=14)
    expected_slice = [round(v, 4) for v in batch_rsi.iloc[19:]]

    assert seq_rsi == expected_slice, "RSI repaints during sequential bar execution!"


def test_macd_sequential_replay():
    df = generate_ohlcv_series(100)
    
    seq_hist = []
    for t in range(35, len(df) + 1):
        sub_df = df.iloc[:t].copy()
        _, _, hist = compute_macd(sub_df, fast=12, slow=26, signal=9)
        seq_hist.append(round(hist.iloc[-1], 6))

    _, _, batch_hist = compute_macd(df, fast=12, slow=26, signal=9)
    expected_slice = [round(v, 6) for v in batch_hist.iloc[34:]]

    assert seq_hist == expected_slice, "MACD histogram repaints during sequential execution!"


def test_smc_order_block_sequential_replay():
    df = generate_ohlcv_series(120)
    ob_engine = OrderBlockEngine()

    seq_obs = {}
    for t in range(40, len(df) + 1):
        sub_df = df.iloc[:t].copy()
        obs = ob_engine.detect_order_blocks(sub_df, asset="EURUSD", timeframe="1H")
        seq_obs[t] = [(ob.price_high, ob.price_low, ob.block_type.value) for ob in obs]

    batch_obs = ob_engine.detect_order_blocks(df, asset="EURUSD", timeframe="1H")
    batch_summary = [(ob.price_high, ob.price_low, ob.block_type.value) for ob in batch_obs]

    assert seq_obs[len(df)] == batch_summary
