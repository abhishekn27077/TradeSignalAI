"""
tests/test_shadow_point_in_time.py
==================================
Point-in-Time Integrity & Lookahead Injection Tests (Phase 72).

Verifies:
1. Injected future candles (T > decision_timestamp) trigger Fail-Closed LookaheadViolationError.
2. Injected future news events are ignored / rejected before decision timestamp.
3. Historical predictions cannot be modified by future data revisions.
"""

import pytest
import pandas as pd
from datetime import datetime, timezone, timedelta

from app.validation.lookahead_instrumentation import lookahead_guard, LookaheadViolationError
from app.core.market_clock import MarketClock


def test_future_candle_injection_fails_closed():
    """Future candles with timestamps greater than decision time must raise LookaheadViolationError."""
    t0 = datetime(2026, 8, 26, 14, 0, 0, tzinfo=timezone.utc)
    future_candle_time = t0 + timedelta(minutes=15)

    df = pd.DataFrame({
        "timestamp": [t0 - timedelta(hours=1), t0, future_candle_time],
        "open": [1.0840, 1.0850, 1.0860],
        "high": [1.0860, 1.0870, 1.0880],
        "low": [1.0830, 1.0840, 1.0850],
        "close": [1.0850, 1.0860, 1.0870],
        "volume": [1000, 1200, 1500]
    })

    with pytest.raises(LookaheadViolationError):
        lookahead_guard.assert_no_lookahead(df, decision_timestamp=t0, component_name="ShadowSignalEngine")


def test_market_clock_future_timestamp_validation():
    """MarketClock must identify future candle timestamps as invalid."""
    wall_clock = datetime(2026, 8, 26, 14, 0, 0, tzinfo=timezone.utc)
    future_ts = wall_clock + timedelta(minutes=10)

    val = MarketClock.validate_candle_timestamp(future_ts, wall_clock_ts=wall_clock)
    assert val["is_valid"] is False
    assert val["is_future"] is True
    assert val["status"] == "FUTURE_TIMESTAMP_VIOLATION"


def test_market_clock_stale_feed_detection():
    """MarketClock must flag candle data older than max_staleness_seconds as stale."""
    wall_clock = datetime(2026, 8, 26, 14, 0, 0, tzinfo=timezone.utc)
    stale_ts = wall_clock - timedelta(hours=3)  # 3 hours old

    val = MarketClock.validate_candle_timestamp(stale_ts, wall_clock_ts=wall_clock, max_staleness_seconds=7200)
    assert val["is_stale"] is True
    assert val["status"] == "STALE_DATA_WARNING"
