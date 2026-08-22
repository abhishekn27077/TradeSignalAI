"""
tests/test_phase37_h4_pipeline.py
=================================
Validates H4 forecast pipeline, candle boundary calculation, feature calculation,
and Kronos model integration on closed candles.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone

from app.core.timing import CandleClock
from app.analytics.feature_engine import FeatureEngine
from app.analytics.consensus_engine import ConsensusEngine
from app.strategies.strategy_engine.regime_detector import MarketRegimeDetector


def test_h4_candle_boundary_discipline():
    status = CandleClock.get_candle_status("H4")
    assert status["timeframe"] == "H4"
    assert "current_candle_close_ist" in status
    assert "current_candle_close_utc" in status
    assert status["remaining_seconds"] >= 0
    assert len(status["countdown"]) == 8  # HH:MM:SS


def test_feature_engine_no_row_drop():
    # Test that 60 bars are enriched without dropna wiping the dataset
    dates = pd.date_range(end=datetime.now(timezone.utc), periods=60, freq="4h")
    df = pd.DataFrame({
        "open": np.linspace(100, 110, 60),
        "high": np.linspace(101, 112, 60),
        "low": np.linspace(99, 109, 60),
        "close": np.linspace(100.5, 111, 60),
        "volume": np.random.uniform(1000, 5000, 60)
    }, index=dates)
    
    enriched = FeatureEngine.add_all_features(df)
    assert len(enriched) == 60, f"Expected 60 rows, got {len(enriched)}"
    assert "RSI_14" in enriched.columns
    assert "MACD" in enriched.columns
    assert "ATR_14" in enriched.columns
    assert "EMA_20" in enriched.columns
    assert "EMA_50" in enriched.columns
    assert "EMA_200" in enriched.columns


def test_regime_detection():
    dates = pd.date_range(end=datetime.now(timezone.utc), periods=60, freq="4h")
    df = pd.DataFrame({
        "open": np.linspace(100, 120, 60),
        "high": np.linspace(101, 122, 60),
        "low": np.linspace(99, 119, 60),
        "close": np.linspace(100.5, 121, 60),
        "volume": np.random.uniform(1000, 5000, 60)
    }, index=dates)
    enriched = FeatureEngine.add_all_features(df)
    
    regime = MarketRegimeDetector().detect_regime(enriched)
    assert isinstance(regime, str)
    assert len(regime) > 0


def test_consensus_engine_execution():
    dates = pd.date_range(end=datetime.now(timezone.utc), periods=60, freq="4h")
    df = pd.DataFrame({
        "open": np.linspace(100, 105, 60),
        "high": np.linspace(101, 106, 60),
        "low": np.linspace(99, 104, 60),
        "close": np.linspace(100.2, 105.1, 60),
        "volume": np.random.uniform(1000, 5000, 60)
    }, index=dates)
    enriched = FeatureEngine.add_all_features(df)
    
    res = ConsensusEngine().generate_consensus("BTCUSD", "4H", enriched)
    assert "signal" in res
    assert "agreement_percentage" in res
    assert "breakdown" in res
    assert "kronos" in res["breakdown"]
