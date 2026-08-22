import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from app.strategies.SmartMoney.FVG.fvg_engine import (
    FVGEngine, FairValueGap, FVGStatus
)
from app.strategies.Structure.models import Direction


@pytest.fixture
def fvg_test_data():
    """Generates 3-candle sequence creating an obvious bullish FVG."""
    n = 20
    dates = [datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc) + timedelta(hours=i) for i in range(n)]

    opens = [100.0] * n
    highs = [101.0] * n
    lows = [99.0] * n
    closes = [100.0] * n

    # Candle 5: high is 102.0
    highs[5] = 102.0
    lows[5] = 99.5
    closes[5] = 101.5

    # Candle 6: Large green expansion bar
    opens[6] = 101.6
    highs[6] = 108.0
    lows[6] = 101.5
    closes[6] = 107.5

    # Candle 7: Low is 104.0 (gap between candle 5 High 102.0 and candle 7 Low 104.0)
    opens[7] = 107.5
    highs[7] = 110.0
    lows[7] = 104.0
    closes[7] = 109.0

    for i in range(8, n):
        opens[i] = 108.0
        highs[i] = 109.0
        lows[i] = 107.0
        closes[i] = 108.0

    return pd.DataFrame({
        'timestamp': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': [1000] * n
    })


def test_fvg_engine(fvg_test_data):
    engine = FVGEngine(min_atr_multiple=0.1)
    fvgs = engine.detect_fvgs(fvg_test_data, asset="EURUSD", timeframe="1H")

    assert len(fvgs) > 0
    bull_fvgs = [f for f in fvgs if f.direction == Direction.BULLISH]
    assert len(bull_fvgs) >= 1

    gap = bull_fvgs[0]
    assert gap.gap_high > gap.gap_low
    assert gap.gap_size > 0
    assert gap.status in [FVGStatus.ACTIVE, FVGStatus.PARTIALLY_FILLED, FVGStatus.FULLY_FILLED, FVGStatus.INVALIDATED]
