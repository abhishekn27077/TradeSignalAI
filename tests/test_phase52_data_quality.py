import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from app.market_data.quality.engine import (
    TimestampValidator,
    OHLCConsistencyValidator,
    DuplicateDetector,
    VolumeValidator,
    OutlierDetector,
    DataFreshnessMonitor,
    DataQualityEngine
)
from app.market_data.quality.models import DataQualityState


def test_data_quality_clean_dataset():
    n_bars = 50
    now = datetime.now(timezone.utc)
    timestamps = [now - timedelta(hours=50 - i) for i in range(n_bars)]
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'open': [1.1000 + i*0.0001 for i in range(n_bars)],
        'high': [1.1010 + i*0.0001 for i in range(n_bars)],
        'low': [1.0990 + i*0.0001 for i in range(n_bars)],
        'close': [1.1005 + i*0.0001 for i in range(n_bars)],
        'volume': [1500 + i*10 for i in range(n_bars)]
    })

    engine = DataQualityEngine(fail_on_stale=False)
    report = engine.evaluate(df, asset="EURUSD", timeframe="1H", current_time_utc=now)

    assert report.state == DataQualityState.DATA_QUALITY_GOOD
    assert report.is_valid_for_trading is True
    assert len(report.issues) == 0


def test_data_quality_ohlc_violations():
    # Corrupt candle with High < Low and Close > High
    df = pd.DataFrame({
        'timestamp': [datetime.now(timezone.utc)],
        'open': [1.1000],
        'high': [1.0900],  # High < Low (Corrupted!)
        'low': [1.0950],
        'close': [1.1100], # Close > High
        'volume': [1000]
    })

    issues = OHLCConsistencyValidator.validate(df)
    assert len(issues) >= 1
    assert any(i.issue_type == "HIGH_LESS_THAN_LOW" for i in issues)


def test_data_quality_future_timestamps():
    future_time = datetime.now(timezone.utc) + timedelta(days=10)
    df = pd.DataFrame({
        'timestamp': [datetime.now(timezone.utc), future_time],
        'open': [1.1000, 1.1010],
        'high': [1.1020, 1.1030],
        'low': [1.0980, 1.0990],
        'close': [1.1005, 1.1015],
        'volume': [1000, 1200]
    })

    issues = TimestampValidator.validate(df)
    assert any(i.issue_type == "FUTURE_TIMESTAMPS_DETECTED" for i in issues)


def test_data_quality_duplicate_and_negative_volume():
    now = datetime.now(timezone.utc)
    df = pd.DataFrame({
        'timestamp': [now, now],  # duplicate!
        'open': [1.1000, 1.1000],
        'high': [1.1020, 1.1020],
        'low': [1.0980, 1.0980],
        'close': [1.1005, 1.1005],
        'volume': [-50, 100]  # negative volume!
    })

    dup_issues = DuplicateDetector.validate(df)
    vol_issues = VolumeValidator.validate(df)

    assert any(i.issue_type == "DUPLICATE_TIMESTAMPS" for i in dup_issues)
    assert any(i.issue_type == "NEGATIVE_VOLUME" for i in vol_issues)


def test_data_quality_staleness_fails_closed():
    old_time = datetime.now(timezone.utc) - timedelta(hours=10)
    df = pd.DataFrame({
        'timestamp': [old_time],
        'open': [1.1000],
        'high': [1.1020],
        'low': [1.0980],
        'close': [1.1005],
        'volume': [1000]
    })

    engine = DataQualityEngine(fail_on_stale=True)
    report = engine.evaluate(df, asset="EURUSD", timeframe="1H")

    assert report.state == DataQualityState.DATA_STALE
    assert report.is_valid_for_trading is False
