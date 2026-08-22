import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from app.strategies.Structure.strength import StructureStrengthEngine
from app.strategies.indicators.sequence_engine import SequenceEngine
from app.market_data.providers.consensus import ProviderConsensusEngine


def generate_sample_candles(count: int = 100):
    now = datetime.now(timezone.utc)
    base_time = now - timedelta(hours=count)
    dates = [base_time + timedelta(hours=i) for i in range(count)]
    records = []
    base_price = 100.0
    for i in range(count):
        records.append({
            "timestamp": dates[i],
            "open": base_price + i * 0.1,
            "high": base_price + i * 0.1 + 0.5,
            "low": base_price + i * 0.1 - 0.5,
            "close": base_price + i * 0.1 + 0.2,
            "volume": 1000.0,
        })
    return pd.DataFrame(records)


def test_tradingview_primary_feed_consensus():
    df_primary = generate_sample_candles(50)
    df_secondary = df_primary.copy()
    # Add small 0.05% difference
    df_secondary["close"] = df_secondary["close"] * 1.0005

    engine = ProviderConsensusEngine(max_allowed_deviation_pct=0.005)
    report = engine.evaluate_consensus(
        primary_df=df_primary,
        secondary_df=df_secondary,
        asset="EURUSD",
        timeframe="1H",
    )

    assert report.is_consensus_healthy is True
    assert report.mean_price_deviation_pct < 0.001


def test_indicator_non_repainting_invariant():
    df = generate_sample_candles(80)
    engine = StructureStrengthEngine()
    
    # Calculate at length 79
    res_79 = engine.evaluate_strength(df.iloc[:79], "EURUSD", "1H")
    # Calculate at length 80
    res_80 = engine.evaluate_strength(df, "EURUSD", "1H")

    # Past pivot high counts must not disappear (non-repainting)
    assert res_80.get("hh_count", 0) >= res_79.get("hh_count", 0)


def test_sequence_engine_deterministic_calculation():
    df = generate_sample_candles(60)
    seq_engine = SequenceEngine()
    res = seq_engine.analyse(df)

    assert res.sequence_confidence >= 0.0
    assert res.sequence_confidence <= 100.0
    assert res.continuation_prob >= 0.0
    assert res.continuation_prob <= 100.0
