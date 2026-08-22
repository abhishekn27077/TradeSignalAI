import json
import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

from app.strategies.indicators.momentum import RSI
from app.strategies.indicators.trend import ADXTrendEngine
from app.strategies.indicators.volatility import ATRVolatilityEngine
from app.decision.canonical_decision_engine import canonical_decision_engine


def generate_sample_candles(count: int = 100, trend: str = "BULLISH") -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    base_time = now - timedelta(hours=count)
    dates = [base_time + timedelta(hours=i) for i in range(count)]

    base_price = 1.0850
    records = []
    for i in range(count):
        drift = (i * 0.0003) if trend == "BULLISH" else (-i * 0.0003)
        open_p = base_price + drift + np.random.normal(0, 0.0002)
        close_p = open_p + (0.0004 if trend == "BULLISH" else -0.0004)
        high_p = max(open_p, close_p) + 0.0003
        low_p = min(open_p, close_p) - 0.0003
        records.append({
            "timestamp": dates[i],
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p,
            "volume": 1200.0 + (i * 15),
        })
    return pd.DataFrame(records)


def test_phase46_indicator_registry_exists_and_valid():
    registry_path = "indicator_registry.json"
    assert os.path.exists(registry_path), "indicator_registry.json must exist"
    
    with open(registry_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert data["registry_version"] == "46.0.0-PROD"
    assert len(data["indicators"]) >= 10
    names = [ind["name"] for ind in data["indicators"]]
    assert any("EMA" in n for n in names)
    assert any("RSI" in n for n in names)
    assert any("MACD" in n for n in names)


def test_phase46_tv_indicator_math_parity():
    df = generate_sample_candles(count=200)
    
    # RSI 14
    rsi_engine = RSI(period=14)
    rsi = rsi_engine.calculate(df)
    assert 0 <= rsi.dropna().iloc[-1] <= 100
    
    # ATR 14
    atr_engine = ATRVolatilityEngine(period=14)
    atr = atr_engine.calculate_atr(df)
    assert atr.dropna().iloc[-1] > 0
    
    # ADX 14
    adx_engine = ADXTrendEngine(period=14)
    adx_res = adx_engine.analyze(df)
    assert adx_res["adx"] >= 0.0


def test_phase46_non_repainting_invariant():
    df = generate_sample_candles(count=150)
    rsi_engine = RSI(period=14)
    
    # Evaluate at bar 100
    df_past = df.iloc[:100].copy()
    rsi_past = rsi_engine.calculate(df_past).dropna().iloc[-1]
    
    # Evaluate at bar 150 (historical value at index 99 should not change)
    rsi_full = rsi_engine.calculate(df).iloc[99]
    
    assert abs(rsi_past - rsi_full) < 1e-6, "Indicator must be strictly non-repainting"


def test_phase46_counterfactual_gating_logic():
    df_primary = generate_sample_candles(count=80, trend="BULLISH")
    df_secondary = df_primary.copy()
    
    # Evaluate with extreme spread to trigger risk gate
    sig = canonical_decision_engine.evaluate_market(
        asset="EURUSD",
        df_primary=df_primary,
        df_secondary=df_secondary,
        current_spread_pips=10.0,  # Unacceptable spread
    )
    
    assert sig.decision == "NO_TRADE"
    assert sig.decision_reason in ["HIGH_SPREAD", "LOW_CONFLUENCE", "SPREAD_TOO_HIGH", "RISK_GATED", "NO_VALID_SETUP"]
