import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from app.market_data.quality.engine import DataQualityEngine
from app.market_data.quality.models import DataQualityState
from app.strategies.SignalQuality.engine import SignalQualityEngine
from app.strategies.SignalQuality.models import SignalGrade, NoTradeReason


def test_adversarial_corrupted_prices_fail_closed():
    # Injected negative price & zero price
    df = pd.DataFrame({
        'timestamp': [datetime.now(timezone.utc)],
        'open': [0.0],
        'high': [1.1000],
        'low': [-1.0500],
        'close': [1.0950],
        'volume': [1000]
    })

    engine = DataQualityEngine()
    report = engine.evaluate(df, asset="EURUSD")

    assert report.state == DataQualityState.DATA_CORRUPTED
    assert report.is_valid_for_trading is False


def test_adversarial_outlier_spike_detection():
    # 50% price spike in single bar
    df = pd.DataFrame({
        'timestamp': [datetime.now(timezone.utc) - timedelta(hours=i) for i in range(10)][::-1],
        'open': [1.1000]*9 + [1.6500],
        'high': [1.1020]*9 + [1.6600],
        'low': [1.0980]*9 + [1.6400],
        'close': [1.1005]*9 + [1.6550],
        'volume': [1000]*10
    })

    engine = DataQualityEngine()
    report = engine.evaluate(df, asset="EURUSD")

    assert any(i.issue_type == "ANOMALOUS_PRICE_SPIKE" for i in report.issues)
    assert report.state == DataQualityState.DATA_QUALITY_DEGRADED


def test_adversarial_signal_gating_on_adversarial_inputs():
    engine = SignalQualityEngine()

    # Zero stop loss distance, corrupted data, wide spread
    eval_res = engine.evaluate_signal_quality(
        asset="EURUSD",
        direction="BUY",
        entry_price=1.1000,
        stop_loss=1.1000,  # Zero distance!
        take_profit=1.1050,
        confluence_score=95.0,
        data_quality_state=DataQualityState.DATA_CORRUPTED,
        current_spread_pips=15.0
    )

    assert eval_res.grade == SignalGrade.NO_TRADE
    assert eval_res.is_actionable is False
    assert NoTradeReason.DATA_CORRUPTED in eval_res.rejection_reasons
    assert NoTradeReason.POOR_RR in eval_res.rejection_reasons
    assert NoTradeReason.HIGH_SPREAD in eval_res.rejection_reasons
