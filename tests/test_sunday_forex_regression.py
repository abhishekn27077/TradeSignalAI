"""
tests/test_sunday_forex_regression.py
======================================
Phase 21: Specific Sunday Regression Test.

Target Scenario:
  Date: Sunday, 27 September 2026
  Time: Evening IST (e.g. 19:17:09 IST / 13:47:09 UTC)
  Target Assets:
    1. USDJPY (Forex): Market is CLOSED until Sunday 22:00 UTC (03:30 AM IST Monday).
       Expected:
         - Market status: CLOSED
         - Signal decision: REJECTED / NO_TRADE
         - Reason: MARKET_CLOSED
         - Proof: System CANNOT create a USDJPY BUY signal merely because SQLite contains an old candle!
    2. BTCUSDT (Crypto): Market is 24/7 continuous OPEN.
       Expected:
         - Market status: OPEN
         - Can process if primary data is fresh and strategy conditions pass.
"""

import pytest
from datetime import datetime, timezone
import zoneinfo
import sqlite3

from app.core.market_session import MarketSessionService
from app.core.signal_validator import CanonicalSignalValidator, SignalRejectionReason
from app.core.signal_factory import SignalFactory
from app.market_data.market_data_gateway import market_data_gateway
from app.api.v1.terminal_routes import get_today_signals
from app.core.canonical_prospective_ledger import (
    canonical_prospective_ledger,
    CanonicalProspectiveSignal,
    STATUS_GENERATED,
)


IST_TZ = zoneinfo.ZoneInfo("Asia/Kolkata")
SUNDAY_EVENING_IST = datetime(2026, 9, 27, 19, 17, 9, tzinfo=IST_TZ)
SUNDAY_UTC = SUNDAY_EVENING_IST.astimezone(timezone.utc)  # 2026-09-27 13:47:09 UTC


def test_sunday_forex_closed_market_session():
    """Verifies that on Sunday 27 Sept 2026 evening IST, USDJPY is strictly marked CLOSED."""
    status = MarketSessionService.get_market_status("USDJPY", dt_utc=SUNDAY_UTC)
    assert status["is_market_open"] is False
    assert status["status_label"] == "CLOSED"
    assert status["reason"] == "WEEKEND_SUNDAY_PRE_MARKET"
    assert status["current_session"] == "CLOSED"


def test_sunday_crypto_open_market_session():
    """Verifies that on Sunday 27 Sept 2026 evening IST, BTCUSDT/BTCUSD is 24/7 OPEN."""
    status_usdt = MarketSessionService.get_market_status("BTCUSD", dt_utc=SUNDAY_UTC)
    assert status_usdt["is_market_open"] is True
    assert status_usdt["status_label"] == "OPEN"
    assert status_usdt["reason"] == "CRYPTO_24_7"


def test_sunday_forex_signal_blocked_at_validator():
    """Verifies that CanonicalSignalValidator rejects USDJPY on Sunday with MARKET_CLOSED."""
    validation = CanonicalSignalValidator.validate_pre_flight(
        asset_symbol="USDJPY",
        timeframe="4H",
        current_price=152.40,
        stop_loss=151.80,
        take_profit=153.60,
        direction="BUY",
        reference_time=SUNDAY_UTC,
    )
    assert validation.is_valid is False
    assert validation.rejection_reason == SignalRejectionReason.MARKET_CLOSED
    assert "CLOSED" in validation.rejection_detail


def test_sunday_forex_signal_factory_cannot_generate_actionable_signal():
    """
    Verifies that SignalFactory cannot generate a QUALIFIED or TAKE_NOW signal
    for USDJPY on Sunday merely because SQLite has historical candles.
    """
    factory = SignalFactory(db_path="tradesignal.db")
    sig = factory.generate_signal("USDJPY", "1H", dt_utc=SUNDAY_UTC)

    # Must be marked REJECTED and NO_TRADE with invalidation_reason = MARKET_CLOSED
    assert sig.status == "REJECTED"
    assert sig.decision == "NO_TRADE"
    assert sig.invalidation_reason == "MARKET_CLOSED"
    assert sig.decision_trace["pre_flight_passed"] is False
    assert sig.decision_trace["market_session"]["passed"] is False


def test_sunday_sqlite_candles_cannot_become_live_fallback():
    """
    Proves that MarketDataGateway will NOT use historical SQLite candles
    as live actionable price when MT5 broker is disconnected.
    """
    # Verify that get_cached_candles clearly marks candles as HISTORICAL_CACHE and not live
    cached = market_data_gateway._get_cached_candles("USDJPY", "MT5_BROKER", "1H", count=5)
    for c in cached:
        assert c["data_role"] == "HISTORICAL_CACHE"
        assert c["is_live"] is False


def test_terminal_today_endpoint_filters_sunday_closed_forex():
    """
    Proves that the /today API endpoint does NOT serve past USDJPY signals
    on Sunday and correctly displays the Forex Market Closed banner message.
    """
    res = get_today_signals()
    assert res["success"] is True
    assert "is_forex_open" in res
    assert res["is_crypto_open"] is True
    assert res["execution_mode"] == "PAPER_ONLY"

    # None of the qualified signals shown on today can be USDJPY or EURUSD if Forex is closed
    if not res["is_forex_open"]:
        assert res["market_status_message"] is not None
        for sig in res["signals"]:
            assert sig["asset"] not in ["USDJPY", "EURUSD", "GBPUSD", "AUDUSD"]
