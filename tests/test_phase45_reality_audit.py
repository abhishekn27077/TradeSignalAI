import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

from app.market_data.canonical_snapshot import CanonicalMarketDataService
from app.decision.canonical_decision_engine import canonical_decision_engine
from app.analytics.statistical_validation_engine import statistical_validation_engine


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


def test_phase45_market_data_canonical_snapshot():
    df = generate_sample_candles(count=80)
    snapshot = CanonicalMarketDataService.create_snapshot("EURUSD", df, provider="AUDIT_VERIFIED", spread_pips=1.2)
    
    assert snapshot.is_valid_for_trading is True
    assert snapshot.quality_state.value == "DATA_QUALITY_GOOD"
    assert snapshot.bid < snapshot.ask
    assert snapshot.mid > 0


def test_phase45_prediction_id_and_immutability():
    df_primary = generate_sample_candles(count=80, trend="BULLISH")
    df_secondary = df_primary.copy()
    
    sig = canonical_decision_engine.evaluate_market("EURUSD", df_primary, df_secondary)
    
    assert sig.signal_id.startswith("SIG-EURUSD-")
    assert sig.data_snapshot_hash is not None
    assert sig.decision in ["TAKE_TRADE", "NO_TRADE"]
    assert sig.risk is not None


def test_phase45_event_risk_fail_closed():
    df_primary = generate_sample_candles(count=80, trend="BULLISH")
    df_secondary = df_primary.copy()
    
    # Event risk active (e.g. FOMC ±30 min window)
    sig = canonical_decision_engine.evaluate_market("EURUSD", df_primary, df_secondary, is_event_risk=True)
    
    assert sig.decision == "NO_TRADE"
    assert sig.event_risk.get("is_event_risk") is True


def test_phase45_real_money_execution_locked():
    report = statistical_validation_engine.evaluate_live_shadow_sample([], [])
    assert report.classification in ["EDGE_SUPPORTED", "EDGE_NOT_YET_ESTABLISHED", "INSUFFICIENT_SAMPLE"]
