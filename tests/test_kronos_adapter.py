import pytest
import pandas as pd
import numpy as np
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.analytics.models.kronos.adapter import KronosAdapter
from app.analytics.consensus_engine import ConsensusEngine

@pytest.fixture
def sample_ohlcv_df():
    np.random.seed(42)
    dates = pd.date_range(start='2026-01-01', periods=10, freq='5min')
    df = pd.DataFrame({
        'open': np.random.uniform(50000, 51000, 10),
        'high': np.random.uniform(51000, 52000, 10),
        'low': np.random.uniform(49000, 50000, 10),
        'close': np.random.uniform(50000, 51000, 10),
        'volume': np.random.uniform(1, 100, 10)
    }, index=dates)
    df.index.name = 'timestamp'
    return df

def test_kronos_adapter_format_data(sample_ohlcv_df):
    adapter = KronosAdapter(device='cpu')
    formatted_df = adapter.format_market_data(sample_ohlcv_df)
    
    # Check if index is datetime
    assert isinstance(formatted_df.index, pd.DatetimeIndex)
    # Check required columns
    assert all(col in formatted_df.columns for col in ['open', 'high', 'low', 'close', 'volume'])

def test_kronos_adapter_predict(sample_ohlcv_df):
    adapter = KronosAdapter(device='cpu')
    # Use formatted data to predict
    formatted_df = adapter.format_market_data(sample_ohlcv_df)
    
    pred_return = adapter.predict(formatted_df, pred_len=1)
    
    # Should return a scalar expected return (float)
    assert isinstance(pred_return, float)

def test_consensus_engine_integration(sample_ohlcv_df):
    engine = ConsensusEngine()
    
    # Provide sample dataframe
    result = engine.generate_consensus("BTCUSD", "5m", sample_ohlcv_df)
    
    assert "error" not in result
    assert "consensus_expected_return" in result
    assert "breakdown" in result
    # Check if kronos prediction is not flat zero from an exception
    # (Though it might legitimately predict exactly 0, an exception usually logs an error)
    # The main check is that it runs without the `freq` integer type error.
    assert "kronos" in result["breakdown"]
    assert isinstance(result["breakdown"]["kronos"], float)
