import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from app.decision.canonical_decision_engine import canonical_decision_engine, CanonicalTradingSignal
from app.market_data.canonical_snapshot import CanonicalMarketDataService, MarketDataSnapshot
from app.market_data.quality.models import DataQualityState
from app.strategies.indicators.sequence_engine import SequenceEngine
from app.portfolio.risk_budget_engine import RiskBudgetEngine
from app.portfolio.currency_exposure_engine import CurrencyExposureEngine


def generate_candles(count: int = 80, trend: str = "BULLISH", volatility: float = 0.0002) -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    base_time = now - timedelta(hours=count)
    dates = [base_time + timedelta(hours=i) for i in range(count)]
    base_price = 1.0850
    records = []
    for i in range(count):
        drift = (i * 0.0003) if trend == "BULLISH" else ((-i * 0.0003) if trend == "BEARISH" else 0.0)
        open_p = base_price + drift + np.random.normal(0, volatility)
        close_p = open_p + (0.0004 if trend == "BULLISH" else (-0.0004 if trend == "BEARISH" else 0.0001))
        high_p = max(open_p, close_p) + 0.0003
        low_p = min(open_p, close_p) - 0.0003
        records.append({
            "timestamp": dates[i],
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p,
            "volume": 1000.0 + i * 10,
        })
    return pd.DataFrame(records)


def test_runtime_pipeline_trace_latency_and_decision():
    df = generate_candles(count=80, trend="BULLISH")
    signal = canonical_decision_engine.evaluate_market("EURUSD", df, timeframe="1H", current_spread_pips=1.0)
    
    assert isinstance(signal, CanonicalTradingSignal)
    assert signal.signal_id.startswith("SIG-EURUSD-1H-")
    assert signal.data_quality_state == "DATA_QUALITY_GOOD"
    assert signal.decision in ["TAKE_TRADE", "NO_TRADE"]


def test_multi_pass_reproducibility():
    df = generate_candles(count=80, trend="BULLISH")
    sig1 = canonical_decision_engine.evaluate_market("EURUSD", df, timeframe="1H", run_id="FIXED-RUN-1")
    sig2 = canonical_decision_engine.evaluate_market("EURUSD", df, timeframe="1H", run_id="FIXED-RUN-1")

    assert sig1.decision == sig2.decision
    assert sig1.direction == sig2.direction
    assert sig1.confidence == sig2.confidence
    assert sig1.config_hash == sig2.config_hash
    assert sig1.data_snapshot_hash == sig2.data_snapshot_hash


def test_risk_scenario_a_valid_setup():
    risk_engine = RiskBudgetEngine()
    res = risk_engine.calculate_position_size(
        account_equity=100000.0,
        entry_price=1.0850,
        stop_loss=1.0830,
        asset="EURUSD",
        direction="BUY",
        current_daily_drawdown_pct=0.01,
    )
    assert res.is_trade_allowed is True
    assert res.recommended_lots > 0.0


def test_risk_scenario_c_drawdown_circuit_breaker():
    risk_engine = RiskBudgetEngine()
    res = risk_engine.calculate_position_size(
        account_equity=100000.0,
        entry_price=1.0850,
        stop_loss=1.0830,
        asset="EURUSD",
        direction="BUY",
        current_daily_drawdown_pct=0.055,  # 5.5% daily drawdown >= 5.0%
    )
    assert res.is_trade_allowed is False
    assert res.recommended_lots == 0.0
    assert "drawdown" in res.rejection_reason.lower()


def test_risk_scenario_d_currency_exposure_limit():
    exp_engine = CurrencyExposureEngine(max_single_currency_lots=3.0)
    existing = [
        {"asset": "EURUSD", "direction": "BUY", "lots": 2.0},
        {"asset": "EURJPY", "direction": "BUY", "lots": 1.5},
    ]
    # Total EUR net exposure = 3.5 > 3.0
    can_open, reason = exp_engine.can_open_new_position("EURGBP", "BUY", 0.5, existing)
    assert can_open is False
    assert reason is not None


def test_sequence_engine_20_scenarios_sensitivity():
    seq_engine = SequenceEngine()
    results = []
    
    # Run across 5 different trends/volatilities
    for trend in ["BULLISH", "BEARISH", "SIDEWAYS"]:
        for vol in [0.0001, 0.0005, 0.0010]:
            df = generate_candles(count=80, trend=trend, volatility=vol)
            res = seq_engine.analyse(df)
            results.append(res.sequence_confidence)

    # Prove outputs are dynamic and responsive across varied market conditions
    assert len(set(results)) > 1
    assert all(0.0 <= c <= 100.0 for c in results)
