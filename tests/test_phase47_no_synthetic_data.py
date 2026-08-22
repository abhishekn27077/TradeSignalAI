"""
Phase 47 — Test Suite for No-Synthetic-Data Guard.

Verifies:
  - No fake prices or mock data in live production paths
  - Real candles from historical store are used
  - Real money trading remains strictly disabled
"""
import pytest
from app.config.settings import get_settings
from app.runtime.live_forecast_scheduler import live_forecast_scheduler


class TestNoSyntheticDataGuard:
    def test_real_money_trading_is_disabled(self):
        settings = get_settings()
        assert settings.EXECUTION_MODE != "LIVE", "Real money live trading must remain DISABLED"

    def test_live_scheduler_uses_real_database_candles(self):
        candle = live_forecast_scheduler.fetch_latest_closed_candle("EURUSD")
        assert candle["provider"] == "SQLITE_LIVE_FEED"
        assert candle["close"] > 0
        assert "timestamp" in candle
