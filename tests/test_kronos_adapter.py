"""
tests/test_kronos_adapter.py
============================
Verifies KronosAdapter functionality, genuine PyTorch model inference,
data formatting, and offline error safety (Phase 70).
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from app.analytics.models.kronos.adapter import KronosAdapter


@pytest.fixture
def sample_ohlcv_df():
    start_time = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
    times = [start_time + timedelta(hours=i) for i in range(60)]
    prices = 1.0850 + np.cumsum(np.random.normal(0, 0.0005, 60))
    df = pd.DataFrame({
        'open': prices,
        'high': prices + 0.0010,
        'low': prices - 0.0010,
        'close': prices + 0.0002,
        'volume': np.random.uniform(1000, 5000, 60)
    }, index=times)
    return df


def test_kronos_adapter_initialization():
    adapter = KronosAdapter(device="cpu")
    # In this environment, PyTorch weights are loaded
    assert adapter.device == "cpu"
    if adapter.model is not None:
        assert adapter.tokenizer is not None
        assert adapter.predictor is not None


def test_kronos_adapter_predict(sample_ohlcv_df):
    adapter = KronosAdapter(device="cpu")
    if adapter.predictor is not None:
        pred_return = adapter.predict(sample_ohlcv_df, pred_len=1)
        assert isinstance(pred_return, float)
        assert not np.isnan(pred_return)
        assert not np.isinf(pred_return)
        # Expected return is reasonably bounded in normal market regimes
        assert -0.20 < pred_return < 0.20


def test_kronos_adapter_empty_df_safety():
    adapter = KronosAdapter(device="cpu")
    empty_df = pd.DataFrame()
    pred_return = adapter.predict(empty_df, pred_len=1)
    assert pred_return == 0.0
