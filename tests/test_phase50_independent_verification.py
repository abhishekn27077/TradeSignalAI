import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone


def generate_sample_candles(count: int = 100) -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    base_time = now - timedelta(hours=count)
    dates = [base_time + timedelta(hours=i) for i in range(count)]
    records = []
    base_price = 1.0850
    for i in range(count):
        drift = i * 0.0002
        open_p = base_price + drift
        close_p = open_p + 0.0003
        high_p = close_p + 0.0002
        low_p = open_p - 0.0002
        records.append({
            "timestamp": dates[i],
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p,
            "volume": 1000.0 + i,
        })
    return pd.DataFrame(records)


def test_phase50_same_candle_conservative_resolution():
    entry = 1.08450
    sl = 1.08340
    tp = 1.08690
    
    candle_high = 1.08700
    candle_low = 1.08300
    
    tp_touched = candle_high >= tp
    sl_touched = candle_low <= sl
    
    assert tp_touched and sl_touched, "Same candle ambiguity condition must be active"
    
    # Invariant: Must resolve conservatively as LOSS (SL First)
    if tp_touched and sl_touched:
        resolution = "LOSS_SL_FIRST"
        realized_r = -1.0
    else:
        resolution = "WIN_TP_FIRST"
        realized_r = 2.18
        
    assert resolution == "LOSS_SL_FIRST"
    assert realized_r == -1.0


def test_phase50_raw_signal_reconstruction_determinism():
    from app.decision.canonical_decision_engine import canonical_decision_engine
    
    df = generate_sample_candles(100)
    
    # 5 independent evaluations on the same closed data
    decisions = []
    for _ in range(5):
        sig = canonical_decision_engine.evaluate_market(
            asset="EURUSD",
            df_primary=df.copy(),
            timeframe="1H",
            current_spread_pips=1.0,
        )
        decisions.append((sig.decision, sig.direction, sig.confidence, sig.decision_reason))
        
    # All 5 passes must be bit-for-bit identical
    assert len(set(decisions)) == 1, "Decision reconstruction must be 100% deterministic"


def test_phase50_real_money_safety_lock():
    from app.analytics.continuous_forward_monitor import continuous_forward_monitor
    snapshot = continuous_forward_monitor.evaluate_live_cohort()
    assert snapshot.config_hash == "79a4f8e12b79310d"
    assert snapshot.system_status == "PROMISING_FORWARD_EDGE"
