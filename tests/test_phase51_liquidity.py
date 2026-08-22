import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from app.strategies.SmartMoney.Liquidity.liquidity_engine import (
    LiquidityEngine, LiquidityPool, LiquidityType
)
from app.strategies.SmartMoney.Liquidity.sweep_detector import (
    LiquiditySweepDetector, SweepEvent, SweepType
)
from app.strategies.Structure.models import Direction


@pytest.fixture
def liquidity_data():
    n = 40
    dates = [datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc) + timedelta(hours=i) for i in range(n)]

    opens = [100.0] * n
    highs = [101.0] * n
    lows = [99.0] * n
    closes = [100.0] * n

    # Swing Low 1 at bar 10: Low = 95.0
    lows[10] = 95.0
    closes[10] = 96.0

    # Swing Low 2 at bar 20: Low = 95.05 (EQH / EQL within tolerance)
    lows[20] = 95.05
    closes[20] = 96.2

    # Bullish Sweep at bar 30: Low dips to 94.5 (sweeps 95.0 level), but Close is 96.5 (above 95.0)
    lows[30] = 94.5
    closes[30] = 96.5

    return pd.DataFrame({
        'timestamp': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': [1000] * n
    })


def test_liquidity_engine(liquidity_data):
    engine = LiquidityEngine(tolerance_pct=0.002, swing_len=2)
    pools = engine.find_liquidity_pools(liquidity_data, asset="EURUSD", timeframe="1H")

    assert len(pools) > 0
    eql_pools = [p for p in pools if p.liquidity_type == LiquidityType.EQUAL_LOWS]
    assert len(eql_pools) >= 1


def test_sweep_detector(liquidity_data):
    detector = LiquiditySweepDetector(tolerance_pct=0.002)
    sweeps = detector.detect_sweeps(liquidity_data, asset="EURUSD", timeframe="1H")

    assert len(sweeps) > 0
    bull_sweeps = [s for s in sweeps if s.sweep_type == SweepType.BULLISH_SWEEP]
    assert len(bull_sweeps) >= 1
    assert bull_sweeps[0].requires_confluence is True
