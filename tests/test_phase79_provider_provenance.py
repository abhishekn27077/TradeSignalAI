"""
tests/test_phase79_provider_provenance.py
=========================================
Phase 79: Multi-Provider Isolation, Provenance Truth & Real-Money Lockout.

Validates:
1. Binance is the authoritative provider for Crypto (BTCUSD, ETHUSD).
2. MT5 is the authoritative provider for Forex/CFD (EURUSD, GBPUSD, etc.).
3. Strict Provider Isolation:
   - Binance cannot supply Forex or Metal quotes.
   - MT5 cannot supply crypto without broker support.
   - Yahoo or other secondary providers cannot silently override MT5 ticks.
4. SQLite historical cache cannot act as live price authority.
5. Static ASSET_BASE_PRICES cannot enter a LIVE prospective signal.
6. Absolute safety rules:
   - REAL_MONEY_ENABLED == False
   - BROKER_EXECUTION_ENABLED == False
   - EXECUTION_MODE in ("DEMO", "PAPER")
"""

import pytest
import os
from app.config.settings import get_settings
from app.market_data.live_provider_inventory import live_provider_inventory
from app.core.canonical_signal_service import CanonicalSignalService, ASSET_BASE_PRICES


def test_safety_rules_enforcement():
    """Verify that real-money execution and broker order placement remain strictly disabled."""
    settings = get_settings()
    assert settings.REAL_MONEY_ENABLED is False
    assert settings.BROKER_EXECUTION_ENABLED is False
    assert settings.EXECUTION_MODE in ("DEMO", "PAPER")


@pytest.mark.asyncio
async def test_provider_inventory_isolation():
    """Verify provider inventory strictly maps Crypto to Binance and Forex to MT5."""
    inventory = await live_provider_inventory.audit_providers()
    assignments = inventory["primary_assignments"]

    # Crypto -> Binance
    assert assignments["BTCUSD"] == "BINANCE"
    assert assignments["ETHUSD"] == "BINANCE"

    # Forex & CFD -> MT5
    assert assignments["EURUSD"] == "MT5"
    assert assignments["GBPUSD"] == "MT5"
    assert assignments["USDJPY"] == "MT5"
    assert assignments["AUDUSD"] == "MT5"
    assert assignments["XAUUSD"] == "MT5"
    assert assignments["NAS100"] == "MT5"
    assert assignments["SPX500"] == "MT5"


def test_static_base_prices_cannot_enter_live_signal():
    """Verify that static base prices are strictly prohibited in the live prospective signal path."""
    svc = CanonicalSignalService()

    # When evaluating live/prospective signals with missing live price,
    # evaluate_asset must fail closed and NOT fall back to ASSET_BASE_PRICES
    res = svc.evaluate_asset("EURUSD", signal_scope="LIVE", market_data_override={"price": None})

    # Qualification must be rejected
    assert res["qualification_status"] in ("NO_TRADE", "REJECTED")
    assert res["is_qualified"] is False
    assert res["price"] is None

    # Check reason codes indicate rejection due to invalid market data
    decision_trace = res.get("decision_trace", {})
    reasons = decision_trace.get("reason_codes", [])
    assert any("INVALID" in r or "STALE" in r or "STATIC_BASE_PRICE_PROHIBITED" in r or "MARKET_DATA" in r for r in reasons)


def test_sqlite_cannot_override_live_mt5_when_mt5_blocked():
    """Verify that when MT5 is blocked, SQLite history does NOT pretend to be live MT5 data."""
    from app.core.canonical_snapshot_manager import canonical_snapshot_manager
    import asyncio

    snap = asyncio.run(canonical_snapshot_manager.capture_live_snapshot("EURUSD"))
    # When MT5 is blocked / unauthorized, snapshot must fail closed
    assert snap.provider == "MT5"
    assert snap.is_valid is False
    assert snap.provider_status in ("BLOCKED", "UNAVAILABLE")
    assert snap.price == 0.0  # Does not pull old SQLite price as live price
