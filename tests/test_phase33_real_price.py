"""
tests/test_phase33_real_price.py
Phase 33 — Real price fetch and data freshness tests (live or mocked).
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

from app.core.data_freshness import DataFreshnessChecker


class TestDataFreshnessChecker:

    def test_fresh_data_passes_h4(self):
        now = datetime.now(timezone.utc)
        fresh_ts = (now - timedelta(seconds=30)).isoformat()
        rates = [{"timestamp": fresh_ts, "close": 100.0, "open": 99.0, "high": 101.0, "low": 99.0}]
        result = DataFreshnessChecker.check("BTCUSD", "H4", rates)
        assert result.status == "FRESH"
        assert result.data_age_seconds < 600

    def test_stale_data_blocked_h1(self):
        now = datetime.now(timezone.utc)
        old_ts = (now - timedelta(seconds=400)).isoformat()  # > 300s threshold for H1
        rates = [{"timestamp": old_ts, "close": 100.0}]
        result = DataFreshnessChecker.check("EURUSD", "H1", rates)
        assert result.status == "DATA_STALE"
        assert "400" in result.reason or "EXCEEDS" in result.reason

    def test_stale_data_blocked_d1(self):
        now = datetime.now(timezone.utc)
        old_ts = (now - timedelta(seconds=4000)).isoformat()  # > 3600s for D1
        rates = [{"timestamp": old_ts, "close": 100.0}]
        result = DataFreshnessChecker.check("USDJPY", "D1", rates)
        assert result.status == "DATA_STALE"

    def test_all_four_assets_structure(self):
        """Structure test — validates freshness result has all required fields."""
        now = datetime.now(timezone.utc)
        fresh_ts = (now - timedelta(seconds=10)).isoformat()

        for symbol, tf in [("BTCUSD", "H4"), ("ETHUSD", "H4"), ("EURUSD", "H1"), ("USDJPY", "H1")]:
            rates = [{"timestamp": fresh_ts, "close": 1.0}]
            result = DataFreshnessChecker.check(symbol, tf, rates, provider="test")
            d = result.to_dict()
            assert "status" in d
            assert "data_age_seconds" in d
            assert "latest_candle_ts" in d
            assert "prediction_timestamp_utc" in d
            assert "prediction_timestamp_ist" in d
            assert "IST" in d["prediction_timestamp_ist"], "IST timestamp must contain IST"

    def test_provider_recorded(self):
        now = datetime.now(timezone.utc)
        fresh_ts = (now - timedelta(seconds=5)).isoformat()
        rates = [{"timestamp": fresh_ts, "close": 100.0}]
        result = DataFreshnessChecker.check("BTCUSD", "H4", rates, provider="yfinance")
        assert result.provider == "yfinance"

    def test_result_dict_has_candle_info(self):
        now = datetime.now(timezone.utc)
        fresh_ts = (now - timedelta(seconds=5)).isoformat()
        rates = [{"timestamp": fresh_ts, "close": 100.0}]
        result = DataFreshnessChecker.check("BTCUSD", "H4", rates)
        d = result.to_dict()
        assert "previous_closed_candle" in d
        assert "next_candle_open" in d

    def test_missing_timestamp_in_rate_returns_unavailable(self):
        rates = [{"close": 100.0, "open": 99.0}]  # no timestamp key
        result = DataFreshnessChecker.check("BTCUSD", "H4", rates)
        assert result.status == "UNAVAILABLE"

    def test_empty_rates_unavailable(self):
        result = DataFreshnessChecker.check("BTCUSD", "H4", [])
        assert result.status == "UNAVAILABLE"

    def test_multiple_rates_uses_latest(self):
        """Checker must use the last candle's timestamp, not the first."""
        now = datetime.now(timezone.utc)
        old_ts = (now - timedelta(hours=5)).isoformat()
        fresh_ts = (now - timedelta(seconds=10)).isoformat()
        rates = [
            {"timestamp": old_ts, "close": 99.0},
            {"timestamp": fresh_ts, "close": 100.0},
        ]
        result = DataFreshnessChecker.check("BTCUSD", "H4", rates)
        # Should be FRESH because we use the last (most recent) rate
        assert result.status == "FRESH"
        assert result.data_age_seconds < 60

    def test_freshness_uses_configurable_threshold(self):
        """H1 threshold is 300s, H4 is 600s — test they differ."""
        now = datetime.now(timezone.utc)
        ts_350s_ago = (now - timedelta(seconds=350)).isoformat()
        rates = [{"timestamp": ts_350s_ago, "close": 100.0}]
        result_h1 = DataFreshnessChecker.check("EURUSD", "H1", rates)
        result_h4 = DataFreshnessChecker.check("EURUSD", "H4", rates)
        # 350s is > 300s H1 threshold → DATA_STALE for H1
        assert result_h1.status == "DATA_STALE"
        # 350s is < 600s H4 threshold → FRESH for H4
        assert result_h4.status == "FRESH"
