import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

from app.decision.canonical_decision_engine import CanonicalDecisionEngine, canonical_decision_engine
from app.market_data.canonical_snapshot import CanonicalMarketDataService, MarketDataSnapshot
from app.market_data.quality.models import DataQualityState


def generate_test_candles(count: int = 100, trend: str = "BULLISH") -> pd.DataFrame:
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


def test_canonical_market_data_service():
    df = generate_test_candles(count=80)
    snapshot = CanonicalMarketDataService.create_snapshot("EURUSD", df, timeframe="1H")
    
    assert isinstance(snapshot, MarketDataSnapshot)
    assert snapshot.asset == "EURUSD"
    assert snapshot.quality_state == DataQualityState.DATA_QUALITY_GOOD
    assert snapshot.is_valid_for_trading is True
    assert snapshot.bid < snapshot.mid < snapshot.ask


def test_canonical_decision_engine_evaluation():
    df = generate_test_candles(count=80, trend="BULLISH")
    signal = canonical_decision_engine.evaluate_market(
        asset="EURUSD",
        df_primary=df,
        timeframe="1H",
        current_spread_pips=1.0,
    )

    assert signal.signal_id.startswith("SIG-EURUSD-1H-")
    assert signal.run_id.startswith("RUN-")
    assert signal.source_pipeline == "CANONICAL_QUANT_PIPELINE"
    assert signal.strategy_version == "52.0.0-PROD"
    assert signal.model_version == "52.0.0-ENSEMBLE"
    assert signal.decision in ["TAKE_TRADE", "NO_TRADE"]
    assert signal.data_quality_state == "DATA_QUALITY_GOOD"


def test_canonical_decision_engine_fail_closed_on_corrupted_data():
    df = generate_test_candles(count=80)
    # Corrupt the dataframe (High < Low)
    df.loc[df.index[-1], "high"] = 0.5000
    df.loc[df.index[-1], "low"] = 1.5000

    signal = canonical_decision_engine.evaluate_market(
        asset="EURUSD",
        df_primary=df,
        timeframe="1H",
    )

    assert signal.decision == "NO_TRADE"
    assert "DATA_QUALITY_DATA_CORRUPTED" in signal.decision_reason
    assert signal.direction == "NONE"
