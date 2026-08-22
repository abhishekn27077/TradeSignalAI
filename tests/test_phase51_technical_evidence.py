import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from app.strategies.Technical.technical_evidence_engine import TechnicalEvidenceEngine
from app.strategies.Technical.supertrend import compute_supertrend
from app.strategies.Technical.ut_bot import compute_ut_bot
from app.strategies.Structure.models import Direction


@pytest.fixture
def technical_df():
    n = 60
    dates = [datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc) + timedelta(hours=i) for i in range(n)]
    prices = [100.0 + i * 0.5 for i in range(n)]

    return pd.DataFrame({
        'timestamp': dates,
        'open': [p - 0.2 for p in prices],
        'high': [p + 0.5 for p in prices],
        'low': [p - 0.5 for p in prices],
        'close': prices,
        'volume': [1000 + i * 10 for i in range(n)]
    })


def test_technical_evidence(technical_df):
    engine = TechnicalEvidenceEngine()
    evidence = engine.evaluate_evidence(technical_df, asset="EURUSD", timeframe="1H")

    assert "ATR" in evidence
    assert "ADX" in evidence
    assert "RSI" in evidence
    assert "MACD" in evidence
    assert "SUPERTREND" in evidence
    assert "UT_BOT" in evidence
    assert "VWAP" in evidence

    st = evidence["SUPERTREND"]
    assert st.direction == Direction.BULLISH
    assert st.confidence > 0.5


def test_supertrend_non_repainting(technical_df):
    st_val, st_dir = compute_supertrend(technical_df, period=10, multiplier=3.0)
    assert len(st_val) == len(technical_df)
    assert st_dir.iloc[-1] == 1  # Bullish trend


def test_ut_bot(technical_df):
    stop_val, pos = compute_ut_bot(technical_df, key_value=1.0, atr_period=10)
    assert len(stop_val) == len(technical_df)
    assert pos.iloc[-1] == 1
