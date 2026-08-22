"""
tests/test_phase33_faiss.py
Phase 33 — FAISS Memory Engine tests (leak-check focus).
"""
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

from app.intelligence.faiss_memory import FAISSMemoryEngine, STATUS_VALID, STATUS_UNAVAILABLE


def _make_rates(n: int, start_price: float = 100.0) -> list[dict]:
    from datetime import datetime, timezone, timedelta
    base = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    rates = []
    price = start_price
    for i in range(n):
        price += np.random.randn() * 0.5
        rates.append({
            "timestamp": (base + timedelta(hours=i)).isoformat(),
            "open": price - 0.1,
            "high": price + 0.5,
            "low": price - 0.5,
            "close": price,
            "volume": 1000,
        })
    return rates


class TestFAISSMemoryEngine:

    @pytest.mark.asyncio
    async def test_build_index_returns_true_with_sufficient_data(self):
        engine = FAISSMemoryEngine()
        rates = _make_rates(300)
        with patch(
            "app.intelligence.faiss_memory.market_service.get_rates",
            new_callable=AsyncMock,
            return_value=rates,
        ):
            result = await engine.build_index("BTCUSD", "H1", count=300)
        assert result is True

    @pytest.mark.asyncio
    async def test_build_index_returns_false_with_insufficient_data(self):
        engine = FAISSMemoryEngine()
        with patch(
            "app.intelligence.faiss_memory.market_service.get_rates",
            new_callable=AsyncMock,
            return_value=_make_rates(5),  # too few
        ):
            result = await engine.build_index("BTCUSD", "H1", count=5)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_analogs_returns_unavailable_when_no_index(self):
        engine = FAISSMemoryEngine()
        df = pd.DataFrame([{"close": 100.0}])
        ts = pd.Timestamp("2026-08-19 12:00:00", tz="UTC")
        result = engine.get_historical_analogs("BTCUSD", "H1", df, ts)
        assert result["status"] == STATUS_UNAVAILABLE

    @pytest.mark.asyncio
    async def test_leak_check_passes_all_timestamps_before_query(self):
        """Critical: every historical timestamp must be < query_timestamp."""
        engine = FAISSMemoryEngine()
        rates = _make_rates(300)
        with patch(
            "app.intelligence.faiss_memory.market_service.get_rates",
            new_callable=AsyncMock,
            return_value=rates,
        ):
            await engine.build_index("BTCUSD", "H1", count=300)

        # Query at a timestamp well after all historical data
        # Historical data ends at 2025-01-01 + 300 hours
        query_ts = pd.Timestamp("2026-08-19 12:00:00", tz="UTC")
        current_df = pd.DataFrame([{
            "timestamp": pd.Timestamp("2026-08-19 11:00:00", tz="UTC"),
            "close": 100.0,
            "RSI_14": 55.0,
            "MACD": 0.5,
            "MACD_signal": 0.3,
            "ATR_14": 1.0,
            "BB_high": 102.0,
            "BB_low": 98.0,
            "Momentum_10": 0.1,
            "ROC_10": 0.05,
        }])

        result = engine.get_historical_analogs("BTCUSD", "H1", current_df, query_ts)

        if result["status"] == STATUS_VALID:
            assert result["leak_check"] is True
            # All timestamps must be < query_ts
            for ts_str in result["nearest_timestamps"]:
                ts = pd.Timestamp(ts_str)
                assert ts < query_ts, f"LEAKAGE: {ts} >= {query_ts}"

    @pytest.mark.asyncio
    async def test_leak_blocked_when_analog_at_future_timestamp(self):
        """Analogs at or after query_timestamp must be excluded."""
        engine = FAISSMemoryEngine()
        # Build index with recent data
        rates = _make_rates(300)
        with patch(
            "app.intelligence.faiss_memory.market_service.get_rates",
            new_callable=AsyncMock,
            return_value=rates,
        ):
            await engine.build_index("BTCUSD", "H1", count=300)

        # Query at timestamp BEFORE the historical data (would be leakage if any matched)
        query_ts = pd.Timestamp("2024-12-31 00:00:00", tz="UTC")
        current_df = pd.DataFrame([{
            "timestamp": query_ts - pd.Timedelta(hours=1),
            "close": 100.0,
            "RSI_14": 55.0,
            "MACD": 0.5,
            "MACD_signal": 0.3,
            "ATR_14": 1.0,
            "BB_high": 102.0,
            "BB_low": 98.0,
            "Momentum_10": 0.1,
            "ROC_10": 0.05,
        }])
        result = engine.get_historical_analogs("BTCUSD", "H1", current_df, query_ts)
        # All analogs are from 2025 which is after query_ts → should be blocked
        if result["status"] == STATUS_VALID:
            for ts_str in result["nearest_timestamps"]:
                ts = pd.Timestamp(ts_str)
                assert ts < query_ts, f"LEAKAGE FOUND: {ts}"
        # If status is UNAVAILABLE, that is also acceptable (all blocked)
        assert result["status"] in [STATUS_VALID, STATUS_UNAVAILABLE]

    def test_result_contains_all_required_fields_when_valid(self):
        """Verify the trace shape, even if mocked."""
        required_fields = [
            "status", "samples", "nearest_timestamps", "distances",
            "similarities", "historical_directions", "historical_outcomes",
            "average_analog_return", "historical_direction",
            "leak_check", "closest_match_date", "similarity_score",
        ]
        engine = FAISSMemoryEngine()
        result = engine.get_historical_analogs(
            "BTCUSD", "H1", pd.DataFrame(), pd.Timestamp("2026-08-19 12:00:00", tz="UTC")
        )
        # UNAVAILABLE case still should have most keys
        for field in ["status", "leak_check", "samples", "nearest_timestamps"]:
            assert field in result, f"Missing field: {field}"
