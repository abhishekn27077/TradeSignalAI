import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from app.strategies.SmartMoney.OrderBlocks.order_block_engine import (
    OrderBlockEngine, OrderBlock, BlockType, BlockStatus
)
from app.strategies.Structure.models import Direction


@pytest.fixture
def ob_test_data():
    """Generates candle sequence with a clear down candle followed by strong bullish impulse."""
    n = 30
    dates = [datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc) + timedelta(hours=i) for i in range(n)]

    opens = [100.0] * n
    highs = [100.5] * n
    lows = [99.5] * n
    closes = [100.0] * n

    # Base range
    for i in range(10):
        opens[i] = 100.0 + i * 0.1
        closes[i] = 100.1 + i * 0.1
        highs[i] = closes[i] + 0.3
        lows[i] = opens[i] - 0.3

    # Order block down candle at idx 10
    opens[10] = 101.5
    closes[10] = 100.8  # Down candle
    highs[10] = 101.8
    lows[10] = 100.5

    # Massive bullish impulse at idx 11, 12
    opens[11] = 100.9
    closes[11] = 104.0
    highs[11] = 104.5
    lows[11] = 100.8

    opens[12] = 104.1
    closes[12] = 106.0
    highs[12] = 106.5
    lows[12] = 104.0

    # Retest pullback at idx 15
    for i in range(13, 20):
        opens[i] = 106.0 - (i - 12) * 0.8
        closes[i] = opens[i] - 0.2
        highs[i] = opens[i] + 0.2
        lows[i] = closes[i] - 0.2

    # Candle 17 touches OB (low dips to 101.2)
    lows[17] = 101.2

    return pd.DataFrame({
        'timestamp': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': [1000] * n
    })


def test_order_block_detection_and_mitigation(ob_test_data):
    engine = OrderBlockEngine(swing_len=2, impulse_threshold_atr=1.0)
    obs = engine.detect_order_blocks(ob_test_data, asset="EURUSD", timeframe="1H")

    assert len(obs) > 0
    bullish_obs = [ob for ob in obs if ob.block_type == BlockType.BULLISH_OB]
    first_ob = bullish_obs[0]
    assert first_ob.status in [
        BlockStatus.ACTIVE, BlockStatus.TOUCHED, BlockStatus.PARTIALLY_MITIGATED,
        BlockStatus.FULLY_MITIGATED, BlockStatus.INVALIDATED
    ]
    assert first_ob.touch_count >= 1
