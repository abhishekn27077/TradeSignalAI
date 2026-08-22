import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from app.strategies.Structure.swing import (
    SwingDetector, InternalStructureDetector, SwingStructureDetector
)
from app.strategies.Structure.models import SwingType, StructureType, Direction
from app.strategies.Structure.bos_choch import BOSEngine, CHoCHEngine
from app.strategies.Structure.msb import MSBEngine
from app.strategies.Structure.strength import StructureStrengthEngine


@pytest.fixture
def sample_ohlcv():
    """Generates synthetic trending OHLCV data with distinct swings."""
    np.random.seed(42)
    n = 60
    base_time = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
    dates = [base_time + timedelta(hours=i) for i in range(n)]

    # Up-trend wave followed by down-trend wave
    price = 100.0
    prices = []
    for i in range(n):
        if i < 30:
            price += (np.sin(i / 3.0) * 1.5 + 0.8)
        else:
            price -= (np.sin(i / 3.0) * 1.5 + 0.8)
        prices.append(price)

    df = pd.DataFrame({
        'timestamp': dates,
        'open': [p - 0.2 for p in prices],
        'high': [p + 0.8 for p in prices],
        'low': [p - 0.8 for p in prices],
        'close': prices,
        'volume': [1000 + (i % 5) * 200 for i in range(n)]
    })
    return df


def test_swing_detector(sample_ohlcv):
    detector = SwingDetector(left_len=3, right_len=3)
    swings = detector.detect_swings(sample_ohlcv, asset="EURUSD", timeframe="1H")

    assert len(swings) > 0
    for s in swings:
        assert s.asset == "EURUSD"
        assert s.timeframe == "1H"
        assert s.swing_type in [SwingType.SWING_HIGH, SwingType.SWING_LOW]
        assert s.confirmed is True
        assert s.timestamp_utc.tzinfo == timezone.utc
        assert "IST" in s.timestamp_ist


def test_bos_engine(sample_ohlcv):
    bos_engine = BOSEngine(swing_len=3)
    events = bos_engine.detect_bos(sample_ohlcv, asset="EURUSD", timeframe="1H")

    assert isinstance(events, list)
    for e in events:
        assert e.event_type in [StructureType.BULLISH_BOS, StructureType.BEARISH_BOS]
        assert e.direction in [Direction.BULLISH, Direction.BEARISH]
        assert e.strength > 0
        assert e.invalidation_price > 0


def test_choch_engine(sample_ohlcv):
    choch_engine = CHoCHEngine(swing_len=3)
    events = choch_engine.detect_choch(sample_ohlcv, asset="EURUSD", timeframe="1H")

    assert isinstance(events, list)
    for e in events:
        assert e.event_type in [StructureType.BULLISH_CHOCH, StructureType.BEARISH_CHOCH]
        assert "reversal_from" in e.details


def test_msb_engine(sample_ohlcv):
    msb_engine = MSBEngine(swing_len=3)
    events = msb_engine.detect_msb(sample_ohlcv, asset="EURUSD", timeframe="1H")

    assert isinstance(events, list)


def test_structure_strength(sample_ohlcv):
    strength_engine = StructureStrengthEngine(swing_len=3)
    result = strength_engine.evaluate_strength(sample_ohlcv, asset="EURUSD", timeframe="1H")

    assert 0.0 <= result["score"] <= 100.0
    assert result["state"] in ["STRONG_BULLISH", "WEAK_BULLISH", "RANGE", "WEAK_BEARISH", "STRONG_BEARISH", "UNCERTAIN"]
