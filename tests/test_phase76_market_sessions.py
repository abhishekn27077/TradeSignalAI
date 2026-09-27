"""
tests/test_phase76_market_sessions.py
======================================
Phase 76 Market Session Validation Test Suite.

Verifies:
1. Forex assets (EURUSD, GBPUSD, USDJPY, AUDUSD) return MARKET_CLOSED on Sunday / weekends.
2. Metal assets (XAUUSD) return MARKET_CLOSED on Sunday / weekends.
3. Index CFDs (NAS100, SPX500) return MARKET_CLOSED on Sunday / weekends.
4. Crypto assets (BTCUSD, ETHUSD) return 24/7 continuous OPEN.
5. Signal generation for any closed asset MUST return MARKET_CLOSED and MUST NOT generate a tradable signal.
6. Timezone conversion to IST (Asia/Kolkata) is accurately calculated across sessions.
"""

from datetime import datetime, timezone
import pytest

from app.core.market_session import MarketSessionService, AssetTradingCalendar, IST_TZ
from app.core.signal_validator import CanonicalSignalValidator, SignalRejectionReason
from app.market_data.market_data_gateway import MarketDataGateway


SUPPORTED_ASSETS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD",
    "XAUUSD", "NAS100", "SPX500",
    "BTCUSD", "ETHUSD"
]


class TestPhase76MarketSessions:
    """Rigorous market session validation across all 9 supported instruments."""

    def test_all_supported_assets_have_session_schedules(self):
        for asset in SUPPORTED_ASSETS:
            assert asset in AssetTradingCalendar.ASSET_SCHEDULES, f"Missing schedule definition for {asset}"

    def test_forex_closed_on_sunday_noon_utc(self):
        # Sunday 2026-09-27 at 12:00:00 UTC (before 22:00 UTC open)
        sunday_dt = datetime(2026, 9, 27, 12, 0, 0, tzinfo=timezone.utc)
        forex_assets = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
        for sym in forex_assets:
            status = MarketSessionService.get_market_status(sym, sunday_dt)
            assert status["is_market_open"] is False, f"{sym} should be closed on Sunday 12:00 UTC"
            assert status["status_label"] == "CLOSED"
            assert status["current_session"] == "CLOSED"

    def test_metals_and_indices_closed_on_sunday_noon_utc(self):
        sunday_dt = datetime(2026, 9, 27, 12, 0, 0, tzinfo=timezone.utc)
        traditional_cfds = ["XAUUSD", "NAS100", "SPX500"]
        for sym in traditional_cfds:
            status = MarketSessionService.get_market_status(sym, sunday_dt)
            assert status["is_market_open"] is False, f"{sym} should be closed on Sunday 12:00 UTC"
            assert status["status_label"] == "CLOSED"

    def test_crypto_open_24_7_on_sunday_noon_utc(self):
        sunday_dt = datetime(2026, 9, 27, 12, 0, 0, tzinfo=timezone.utc)
        crypto_assets = ["BTCUSD", "ETHUSD", "BTCUSDT", "ETHUSDT"]
        for sym in crypto_assets:
            status = MarketSessionService.get_market_status(sym, sunday_dt)
            assert status["is_market_open"] is True, f"{sym} must be open 24/7"
            assert status["status_label"] == "OPEN"
            assert status["current_session"] == "24/7_CONTINUOUS"
            assert status["reason"] == "CRYPTO_24_7"

    def test_forex_open_during_weekday_session(self):
        # Wednesday 2026-09-23 at 14:00:00 UTC (active London/NY session)
        wednesday_dt = datetime(2026, 9, 23, 14, 0, 0, tzinfo=timezone.utc)
        forex_assets = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
        for sym in forex_assets:
            status = MarketSessionService.get_market_status(sym, wednesday_dt)
            assert status["is_market_open"] is True, f"{sym} should be open on Wednesday 14:00 UTC"
            assert status["status_label"] == "OPEN"

    def test_signal_generation_blocked_pre_flight_when_market_closed(self):
        sunday_dt = datetime(2026, 9, 27, 12, 0, 0, tzinfo=timezone.utc)
        result = CanonicalSignalValidator.validate_pre_flight(
            asset_symbol="EURUSD",
            timeframe="1h",
            current_price=1.0850,
            stop_loss=1.0800,
            take_profit=1.0950,
            direction="BUY",
            reference_time=sunday_dt,
        )

        assert result.is_valid is False
        assert result.rejection_reason == SignalRejectionReason.MARKET_CLOSED

    def test_ist_timezone_calculation_accuracy(self):
        dt_utc = datetime(2026, 9, 27, 12, 0, 0, tzinfo=timezone.utc)
        status = MarketSessionService.get_market_status("BTCUSD", dt_utc)
        # UTC 12:00 + 5:30 = 17:30 IST (5:30 PM)
        assert "05:30 PM IST" in status["evaluated_at_ist"]
        assert "Sunday, 27 September 2026" in status["evaluated_at_ist"]
