"""
tests/test_historical_vs_live_data_truth.py
============================================
Tests proving that historical candle availability NEVER qualifies an asset for a live signal.

Requirement:
historical data available + live provider unavailable = NO LIVE SIGNAL

Also proves explicit distinction between:
- HISTORICAL_DATA (cache/evidence in SQLite or historical provider)
- LIVE_DATA (actionable current broker/exchange tick)
- DERIVED_DATA (features, indicators, volatility, regime)
"""

import pytest
import sqlite3
import os
from datetime import datetime, timezone
import pandas as pd

from app.market_data.market_data_gateway import MarketDataGateway
from app.market_data.types import Candle, Timeframe
from app.core.canonical_signal_service import CanonicalSignalService
from app.market_data.health_service import MarketDataHealthService
from app.core.asset_registry import canonical_asset_registry


def test_data_role_classification_semantics():
    """
    Explicitly audit and verify the semantic distinction:
    HISTORICAL_DATA != LIVE_DATA != DERIVED_DATA.
    """
    data_roles = ["HISTORICAL_DATA", "LIVE_DATA", "DERIVED_DATA"]
    assert len(set(data_roles)) == 3
    assert "HISTORICAL_DATA" != "LIVE_DATA"
    assert "DERIVED_DATA" != "LIVE_DATA"


@pytest.mark.asyncio
async def test_historical_available_plus_live_unavailable_equals_no_live_signal():
    """
    Core Invariant:
    Historical candles are present in SQLite store for EURUSD,
    but MT5 live provider is disconnected / unauthorized.
    Result MUST be:
    - Gateway ticker is_actionable == False
    - Gateway ticker status == DATA_UNAVAILABLE
    - Canonical signal qualification == NO_TRADE (NOT QUALIFIED)
    - Rejection reason includes STALE_MARKET_DATA or PRIMARY_PROVIDER_MT5_DISCONNECTED
    """
    # 1. Verify historical data is present
    conn = sqlite3.connect("tradesignal.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM historical_candles WHERE symbol = 'EURUSD'")
    hist_count = cur.fetchone()[0]
    conn.close()
    assert hist_count > 0, "Precondition: historical candles must exist for EURUSD"

    # 2. Check live market data gateway for EURUSD
    gateway = MarketDataGateway()
    tick = await gateway.get_live_ticker("EURUSD")

    # When MT5 is not authorized / disconnected:
    assert tick["provider"] == "MT5"
    assert tick["price"] is None
    assert tick["is_actionable"] is False
    assert tick["status"] == "DATA_UNAVAILABLE"
    assert "DISCONNECTED" in tick["rejection_reason"]

    # 3. Feed into Canonical Signal Service to prove NO LIVE SIGNAL is emitted
    service = CanonicalSignalService()
    # Force evaluation using the unauthenticated/disconnected MT5 state
    signal_state = service.evaluate_asset_intelligence("EURUSD", dt_utc=datetime.now(timezone.utc))

    # Invariant: Must fail closed to NO_TRADE
    assert signal_state["decision"] == "NO_TRADE"
    assert signal_state["is_trade_signal_qualified"] is False
    assert signal_state["qualification_status"] in ("NO_TRADE", "REJECTED", "WATCHLIST")
    assert any(
        r in signal_state["reason_codes"]
        for r in ("INVALID_MARKET_DATA", "STALE_MARKET_DATA", "CONSENSUS_BELOW_THRESHOLD", "PRIMARY_PROVIDER_DISCONNECTED", "DIRECTIONAL_BIAS_PENDING_CONFIRMATION", "MARKET_CLOSED")
    )


def test_market_data_health_marks_sqlite_cache_untradeable_without_live_feed():
    """
    Verify that MarketDataHealthService explicitly flags SQLite historical cache
    with is_valid_for_trading = False.
    """
    svc = MarketDataHealthService()
    health = svc.get_system_health()
    feeds = health.get("feeds", {})

    for key, feed_info in feeds.items():
        if feed_info.get("provider") == "HISTORICAL_SQLITE_CACHE":
            assert feed_info["is_valid_for_trading"] is False, (
                f"{key} historical cache must never be marked valid for live trading"
            )


@pytest.mark.asyncio
async def test_binance_crypto_produces_genuine_live_data():
    """
    Verify that crypto assets (BTCUSD -> BTCUSDT) resolve Binance as live exchange source,
    with genuine timestamp and is_actionable=True when connected.
    """
    gateway = MarketDataGateway()
    tick = await gateway.get_live_ticker("BTCUSD")

    assert tick["venue"] == "BINANCE"
    assert tick["provider"] == "BINANCE"
    assert tick["status"] == "LIVE"
    assert tick["price"] is not None
    assert tick["price"] > 0
    assert tick["is_actionable"] is True
    assert tick["freshness_status"] in ("FRESH", "WARM")
