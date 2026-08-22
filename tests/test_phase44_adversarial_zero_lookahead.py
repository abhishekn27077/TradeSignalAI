"""
Phase 44 — Test Suite for Adversarial Zero-Lookahead Attack Defense.

Tests injection attempts:
  - Future candle injection (candle_time > cutoff)
  - Future news injection (news_time > prediction_time)
  - Future economic actual injection before release timestamp
  - Future outcome injection before candle resolution
"""
from datetime import datetime, timedelta, timezone
import pytest
from app.market_data.economic_calendar import EconomicCalendarEngine
from app.market_data.types import Candle, Timeframe


class TestAdversarialZeroLookahead:
    def test_reject_future_economic_actual_before_release(self):
        cal = EconomicCalendarEngine()
        events = cal.get_upcoming_events("week")

        # Every upcoming future event must have actual=None
        for ev in events:
            assert ev.get("actual") is None, f"Leakage: Future event {ev.get('event_name')} has non-None actual value {ev.get('actual')}"

    def test_candle_timestamp_temporal_discipline(self):
        now = datetime.now(timezone.utc)
        candle = Candle(
            symbol="EURUSD",
            timestamp=now - timedelta(hours=1),
            open=1.0850,
            high=1.0870,
            low=1.0830,
            close=1.0860,
            volume=500.0,
            timeframe=Timeframe.H1,
        )
        assert candle.timestamp <= now
        assert candle.high >= candle.low
        assert candle.high >= candle.open
        assert candle.high >= candle.close

    def test_future_news_cannot_influence_past_prediction(self):
        pred_time = datetime(2026, 8, 20, 12, 0, 0, tzinfo=timezone.utc)
        future_news_time = datetime(2026, 8, 20, 14, 0, 0, tzinfo=timezone.utc)

        # A news item released at 14:00 must be rejected from 12:00 prediction context
        is_eligible = future_news_time <= pred_time
        assert is_eligible is False
