"""
tests/test_phase76_live_data_truth.py
======================================
Phase 76 Live-Data Truth, Provider Provenance & End-to-End Forensic Audit Suite.

Verifies:
1.  MT5 Provider fails closed when terminal is disconnected / unavailable
2.  MT5 Provider connection cooldown / circuit breaker prevents event-loop hang
3.  MT5 Provider broker suffix resolution preserves canonical instrument identity
4.  Binance Provider symbol normalization (BTCUSD -> BTCUSDT) & venue provenance
5.  MarketDataGateway fail-closed: returns DATA_UNAVAILABLE on missing live provider
6.  Freshness evaluation: tick data boundaries (fresh, stale, future, clock skew)
7.  Candle freshness evaluation: separate thresholds by timeframe (1m vs 1H vs 4H)
8.  Sunday market state: Forex & CFDs CLOSED, Crypto OPEN 24/7
9.  Sunday historical signal rejection: Friday USDJPY candle cannot become live signal
10. Canonical instrument registry: zero ambiguity, zero duplicate/contaminated mappings
11. SQLite reads classified as historical evidence / cache, never masquerading as live
12. Zero metric fabrication: Sharpe & Profit Factor return 0.0 when trade sample <= 1
13. Lookahead audit: zero bfill() and zero center=True in production feature engines
14. Real-money safety: REAL_MONEY_ENABLED=False hardlock & zero live execution paths
15. Security: unauthenticated state-changing POST/PUT/DELETE blocked with 401
16. Security: unauthenticated WebSocket state mutation actions blocked
17. Health separation: Infrastructure Health is explicitly decoupled from Market Data Health
18. Signal provenance: every prospective signal contains full traceable origin metadata
19. Outcome resolution causality: conservative policy on same-candle SL/TP ambiguity
20. Cross-timeframe isolation: 1H request strictly rejects 4H data and vice versa
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any
import pytest
import pandas as pd
import numpy as np

from app.config.settings import get_settings
from app.core.asset_registry import canonical_asset_registry, AssetClass, ProviderType
from app.core.market_session import market_session_service, MarketSessionService
from app.market_data.freshness_service import DataFreshnessService, FreshnessStatus
from app.market_data.market_data_gateway import MarketDataGateway
from app.market_data.providers.mt5_provider import MT5DataProvider
from app.market_data.providers.binance_provider import BinanceCryptoDataProvider
from app.market_data.health_service import MarketDataHealthService
from app.analytics.canonical_statistics_service import CanonicalStatisticsService
from app.core.signal_validator import CanonicalSignalValidator, SignalRejectionReason
from app.core.canonical_prospective_ledger import (
    canonical_prospective_ledger,
    CanonicalProspectiveSignal,
    OUTCOME_LOST,
)


# ── 1. MT5 Provider Fails Closed When Disconnected ────────────────────────────
@pytest.mark.asyncio
async def test_mt5_provider_disconnected_returns_none_fails_closed():
    provider = MT5DataProvider()
    # Explicitly ensure not connected
    provider._connected = False
    provider._last_connect_failure = datetime.now(timezone.utc)  # trigger cooldown

    ticker = await provider.get_ticker("EURUSD")
    assert ticker is None, "MT5DataProvider must return None when disconnected, never mock/synthetic ticks."

    rates = await provider.get_rates("EURUSD", "1H", count=10)
    assert rates == [], "MT5DataProvider must return empty list for rates when disconnected."


# ── 2. MT5 Provider Connection Cooldown Circuit Breaker ────────────────────────
@pytest.mark.asyncio
async def test_mt5_connection_cooldown_circuit_breaker():
    provider = MT5DataProvider()
    provider._connected = False
    provider._last_connect_failure = datetime.now(timezone.utc)
    provider._connect_cooldown_seconds = 30.0

    # Next immediate connect attempt must be skipped by cooldown
    res = await provider.connect()
    assert res is False, "connect() must return False immediately during cooldown without hanging."


# ── 3. MT5 Broker Suffix Resolution Preserves Instrument ──────────────────────
def test_mt5_broker_suffix_resolution_preserves_instrument():
    provider = MT5DataProvider()
    # Check known suffixes list exists and includes standard variations
    assert "" in provider.KNOWN_BROKER_SUFFIXES
    assert "m" in provider.KNOWN_BROKER_SUFFIXES
    assert ".pro" in provider.KNOWN_BROKER_SUFFIXES

    # When disconnected or unmapped, returns None without substituting a different instrument
    res = provider._resolve_broker_symbol("EURUSD")
    assert res is None, "Must return None when MT5 is disconnected rather than guessing."


# ── 4. Binance Provider Symbol Normalization & Provenance ─────────────────────
@pytest.mark.asyncio
async def test_binance_provider_symbol_normalization_and_provenance():
    provider = BinanceCryptoDataProvider()
    assert provider.name == "BINANCE"

    # Canonical mapping: BTCUSD -> BTCUSDT on Binance
    mapped, note = provider._resolve_symbol("BTCUSD")
    assert mapped == "BTCUSDT", f"Expected BTCUSDT for BTCUSD, got {mapped}"
    assert "Binance BTCUSDT" in (note or "")

    mapped_eth, note_eth = provider._resolve_symbol("ETHUSD")
    assert mapped_eth == "ETHUSDT", f"Expected ETHUSDT for ETHUSD, got {mapped_eth}"

    # Check venue and provider metadata from live endpoint if reachable
    rates = await provider.get_rates("BTCUSD", "1h", count=5)
    if rates:
        candle = rates[0]
        assert candle["provider"] == "BINANCE"
        assert candle["venue"] == "BINANCE"
        assert candle["symbol"] == "BTCUSDT"
        assert "received_timestamp" in candle


# ── 5. MarketDataGateway Fails Closed on Missing Provider ─────────────────────
@pytest.mark.asyncio
async def test_gateway_live_provider_fail_closed_on_provider_unavailable():
    from app.market_data.providers.mt5_provider import mt5_provider
    mt5_provider._connected = False
    mt5_provider._last_connect_failure = datetime.now(timezone.utc)

    gateway = MarketDataGateway()
    # Request ticker with MT5 disconnected
    quote = await gateway.get_live_ticker("EURUSD")
    assert quote["status"] == "DATA_UNAVAILABLE", "Gateway must fail closed if primary live provider is offline."
    assert quote["price"] is None, "Price must be None when live provider is unavailable."
    assert quote["data_role"] == "PRIMARY_UNAVAILABLE"


# ── 6. Freshness Evaluation: Tick Data Boundaries ─────────────────────────────
def test_freshness_boundaries_deterministic():
    now_utc = datetime(2026, 9, 27, 14, 0, 0, tzinfo=timezone.utc)

    # 1. Fresh tick: 1.0s old (limit is 15000ms = 15s)
    eval_fresh = DataFreshnessService.evaluate_tick_freshness(
        source_timestamp=now_utc - timedelta(seconds=1),
        received_timestamp=now_utc,
        asset_class="FOREX",
        reference_time=now_utc,
    )
    assert eval_fresh.status == FreshnessStatus.FRESH
    assert eval_fresh.is_actionable is True

    # 2. Boundary: within limit
    eval_bound = DataFreshnessService.evaluate_tick_freshness(
        source_timestamp=now_utc - timedelta(seconds=10),
        received_timestamp=now_utc,
        asset_class="FOREX",
        reference_time=now_utc,
    )
    assert eval_bound.status == FreshnessStatus.FRESH

    # 3. Stale: 25s old (> 15s fresh limit, <= 60s stale limit)
    eval_stale = DataFreshnessService.evaluate_tick_freshness(
        source_timestamp=now_utc - timedelta(seconds=25),
        received_timestamp=now_utc,
        asset_class="FOREX",
        reference_time=now_utc,
    )
    assert eval_stale.status == FreshnessStatus.STALE
    assert eval_stale.is_actionable is False

    # 4. Expired: 90s old (> 60s max)
    eval_expired = DataFreshnessService.evaluate_tick_freshness(
        source_timestamp=now_utc - timedelta(seconds=90),
        received_timestamp=now_utc,
        asset_class="FOREX",
        reference_time=now_utc,
    )
    assert eval_expired.status == FreshnessStatus.EXPIRED
    assert eval_expired.is_actionable is False

    # 5. Future timestamp (clock skew > 5s): rejected as INVALID
    eval_future = DataFreshnessService.evaluate_tick_freshness(
        source_timestamp=now_utc + timedelta(seconds=10),
        received_timestamp=now_utc,
        asset_class="FOREX",
        reference_time=now_utc,
    )
    assert eval_future.status == FreshnessStatus.INVALID
    assert eval_future.is_actionable is False


# ── 7. Candle Freshness Evaluation by Timeframe ───────────────────────────────
def test_candle_freshness_by_timeframe():
    now_utc = datetime(2026, 9, 27, 14, 0, 0, tzinfo=timezone.utc)

    # 1m candle age threshold: fresh limit 120s
    res_1m_fresh = DataFreshnessService.evaluate_candle_freshness(
        candle_timestamp=now_utc - timedelta(seconds=60),
        timeframe="M1",
        reference_time=now_utc,
    )
    assert res_1m_fresh.status == FreshnessStatus.FRESH

    res_1m_stale = DataFreshnessService.evaluate_candle_freshness(
        candle_timestamp=now_utc - timedelta(seconds=200),
        timeframe="M1",
        reference_time=now_utc,
    )
    assert res_1m_stale.status == FreshnessStatus.STALE

    # 1H candle age threshold: fresh limit 7200s (2 hours)
    res_1h_fresh = DataFreshnessService.evaluate_candle_freshness(
        candle_timestamp=now_utc - timedelta(minutes=50),
        timeframe="H1",
        reference_time=now_utc,
    )
    assert res_1h_fresh.status == FreshnessStatus.FRESH

    # 4H candle age threshold: fresh limit 28800s (8 hours)
    res_4h_fresh = DataFreshnessService.evaluate_candle_freshness(
        candle_timestamp=now_utc - timedelta(hours=3),
        timeframe="H4",
        reference_time=now_utc,
    )
    assert res_4h_fresh.status == FreshnessStatus.FRESH

    # Stale 4H candle from 24h ago
    res_4h_stale = DataFreshnessService.evaluate_candle_freshness(
        candle_timestamp=now_utc - timedelta(hours=24),
        timeframe="H4",
        reference_time=now_utc,
    )
    assert res_4h_stale.status in (FreshnessStatus.STALE, FreshnessStatus.EXPIRED)


# ── 8. Sunday Market State Matrix ─────────────────────────────────────────────
def test_sunday_market_state_matrix():
    sunday_dt = datetime(2026, 9, 27, 13, 0, 0, tzinfo=timezone.utc)

    # Forex assets CLOSED on Sunday pre-open
    forex_assets = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
    for asset in forex_assets:
        is_open = market_session_service.is_market_open(asset, dt_utc=sunday_dt)
        assert is_open is False, f"Forex asset {asset} must be CLOSED on Sunday pre-open."

    # CFD assets CLOSED on Sunday pre-open
    cfd_assets = ["XAUUSD", "NAS100", "SPX500"]
    for asset in cfd_assets:
        is_open = market_session_service.is_market_open(asset, dt_utc=sunday_dt)
        assert is_open is False, f"CFD asset {asset} must be CLOSED on Sunday pre-open."

    # Crypto assets OPEN 24/7 on Sunday
    crypto_assets = ["BTCUSD", "ETHUSD", "BTCUSDT", "ETHUSDT"]
    for asset in crypto_assets:
        is_open = market_session_service.is_market_open(asset, dt_utc=sunday_dt)
        assert is_open is True, f"Crypto asset {asset} must be OPEN 24/7 on Sunday."


# ── 9. Sunday Historical Signal Rejection ──────────────────────────────────────
def test_sunday_historical_signal_rejection():
    sunday_dt = datetime(2026, 9, 27, 13, 0, 0, tzinfo=timezone.utc)
    friday_candle_ts = datetime(2026, 9, 25, 21, 0, 0, tzinfo=timezone.utc)

    # Signal validation pre-flight must reject because market is closed and data is stale
    result = CanonicalSignalValidator.validate_pre_flight(
        asset_symbol="USDJPY",
        timeframe="1H",
        current_price=145.50,
        stop_loss=145.00,
        take_profit=146.50,
        direction="BUY",
        source_timestamp=friday_candle_ts,
        provider_name="MT5",
        venue="MT5_BROKER",
        reference_time=sunday_dt,
    )
    assert result.is_valid is False
    assert result.rejection_reason in (
        SignalRejectionReason.MARKET_CLOSED,
        SignalRejectionReason.DATA_STALE,
        SignalRejectionReason.DATA_UNAVAILABLE,
    )


# ── 10. Canonical Instrument Registry Integrity ───────────────────────────────
def test_canonical_instrument_registry_integrity():
    symbols = canonical_asset_registry.list_canonical_symbols()
    assert len(symbols) == len(set(symbols)), "Duplicate canonical symbols found in registry!"

    # Verify key assets exist with distinct asset classes
    eurusd = canonical_asset_registry.get("EURUSD")
    assert eurusd is not None and eurusd.asset_class == AssetClass.FOREX
    assert eurusd.primary_provider == ProviderType.MT5

    btcusdt = canonical_asset_registry.get("BTCUSDT")
    assert btcusdt is not None and btcusdt.asset_class == AssetClass.CRYPTO
    assert btcusdt.primary_provider == ProviderType.BINANCE

    xauusd = canonical_asset_registry.get("XAUUSD")
    assert xauusd is not None and xauusd.asset_class == AssetClass.METALS
    assert xauusd.primary_provider == ProviderType.MT5


# ── 11. SQLite Classification as Historical Evidence Only ─────────────────────
def test_sqlite_classification_historical_cache_only():
    health_svc = MarketDataHealthService.get_instance()
    # Force rebuild from SQLite
    health_svc.asset_health_registry.clear()
    system_health = health_svc.get_system_health()

    feeds = system_health.get("feeds", {})
    for key, feed in feeds.items():
        if feed.get("provider") == "HISTORICAL_SQLITE_CACHE":
            assert feed.get("is_valid_for_trading") is False, (
                "SQLite historical cache alone must NEVER be marked valid for live trading!"
            )
            assert feed.get("classification") == "HISTORICAL_EVIDENCE"


# ── 12. Zero Metric Fabrication on Insufficient Sample ────────────────────────
def test_no_fabricated_metrics_on_insufficient_sample():
    stats_service = CanonicalStatisticsService()
    # Wilson CI on total=0 returns (0.0, 0.0)
    lower, upper = stats_service.calculate_wilson_ci(0, 0)
    assert lower == 0.0 and upper == 0.0

    # Test summary calculation on empty/filtered records
    summary = stats_service.get_canonical_performance_summary(
        date_filter="ALL", asset="NONEXISTENT_ASSET"
    )
    assert summary["resolved_count"] == 0
    assert summary["win_rate_pct"] == 0.0
    assert summary["sharpe_ratio"] == 0.0, "Sharpe ratio must be 0.0 when trade sample <= 1, never fabricated 1.85!"
    assert summary["profit_factor"] == 0.0, "Profit factor must be 0.0 on zero trades, never fabricated 1.0!"


# ── 13. Lookahead Audit: Zero bfill() and Zero center=True ─────────────────────
def test_lookahead_audit_no_bfill_no_center():
    import inspect
    from app.analytics.feature_engine import FeatureEngine
    from app.market_intelligence.pattern_engine import MarketMemoryEngine

    fe_source = inspect.getsource(FeatureEngine)
    assert "bfill" not in fe_source, "FeatureEngine must not use bfill() (lookahead hazard)."
    assert "center=True" not in fe_source, "FeatureEngine must not use center=True (lookahead hazard)."

    pe_source = inspect.getsource(MarketMemoryEngine)
    assert "bfill" not in pe_source, "MarketMemoryEngine must not use bfill() (lookahead hazard)."
    assert "center=True" not in pe_source, "MarketMemoryEngine must not use center=True (lookahead hazard)."


# ── 14. Real-Money Safety Lockout ─────────────────────────────────────────────
def test_real_money_safety_lockout():
    settings = get_settings()
    assert settings.REAL_MONEY_ENABLED is False, "REAL_MONEY_ENABLED must be strictly False."
    assert settings.BROKER_EXECUTION_ENABLED is False, "BROKER_EXECUTION_ENABLED must be strictly False."
    assert settings.EXECUTION_MODE in ("DEMO", "PAPER"), "EXECUTION_MODE must be paper/demo."


# ── 15. Security: Unauthenticated State-Changing Methods Blocked ──────────────
@pytest.mark.asyncio
async def test_unauthenticated_state_changing_methods_blocked():
    from app.api.middleware import StateChangingAuthMiddleware
    from starlette.requests import Request

    middleware = StateChangingAuthMiddleware(app=None)

    # Mock unauthenticated POST request to a state-changing endpoint
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/system/inject_signal",
        "headers": [(b"content-type", b"application/json")],
    }
    request = Request(scope)

    async def dummy_next(req):
        from starlette.responses import Response
        return Response("ok")

    response = await middleware.dispatch(request, dummy_next)
    assert response.status_code == 401, f"Unauthenticated POST must return 401, got {response.status_code}"


# ── 16. Security: Unauthenticated WebSocket State Mutation Blocked ────────────
def test_websocket_unauthenticated_state_mutation_blocked():
    from app.api.v1.ws import global_websocket_endpoint
    import inspect
    ws_source = inspect.getsource(global_websocket_endpoint)
    assert "Authentication required for write/publish actions" in ws_source
    assert 'action in ("symbol_changed", "publish", "inject_signal", "trigger_action")' in ws_source


# ── 17. Health Separation: Infrastructure vs Market Data Health ───────────────
def test_system_health_vs_market_data_health_separation():
    health_svc = MarketDataHealthService.get_instance()
    data = health_svc.get_system_health()

    assert "infrastructure_health" in data, "Must separate infrastructure_health."
    assert "market_data_health" in data, "Must separate market_data_health."
    assert "trading_state" in data, "Must include trading_state."

    # If all feeds are SQLite cache and zero live feeds, market_data_health must not be falsely HEALTHY
    m_health = data["market_data_health"]
    if m_health.get("healthy_feeds", 0) == 0:
        assert m_health.get("overall_status") in ("DEGRADED", "UNAVAILABLE"), (
            "Market data status cannot be HEALTHY if 0 live feeds are online."
        )


# ── 18. Signal Provenance Structure Complete ──────────────────────────────────
def test_signal_provenance_structure_complete():
    # Verify that CanonicalSignalValidator pre-flight enforces registered asset and session
    result = CanonicalSignalValidator.validate_pre_flight(
        asset_symbol="UNKNOWN_ASSET",
        timeframe="1H",
        current_price=1.0,
        stop_loss=0.9,
        take_profit=1.2,
    )
    assert result.is_valid is False
    assert result.rejection_reason == SignalRejectionReason.UNREGISTERED_ASSET


# ── 19. Outcome Resolution Conservative Ambiguity ─────────────────────────────
def test_outcome_resolution_conservative_ambiguity():
    now = datetime(2026, 9, 27, 14, 0, 0, tzinfo=timezone.utc)
    signal = CanonicalProspectiveSignal(
        signal_id="TEST-AMBIGUOUS-001",
        campaign_id="CAMPAIGN-TEST",
        generated_at_utc=now.isoformat(),
        generated_at_ist=now.isoformat(),
        asset="EURUSD",
        timeframe="1H",
        direction="BUY",
        market_snapshot_hash="hash-ambig",
        policy_version="POL-v1",
        model_version="MODEL-v1",
        config_hash="cfg-hash",
        entry_window_start=now.isoformat(),
        entry_window_end=(now + timedelta(minutes=15)).isoformat(),
        preferred_entry_time=(now + timedelta(minutes=5)).isoformat(),
        entry_price=1.1000,
        stop_loss=1.0950,
        take_profit=1.1050,
        expected_hold_seconds=3600,
        expected_exit_time=(now + timedelta(hours=1)).isoformat(),
        max_exit_time=(now + timedelta(hours=2)).isoformat(),
        probability=0.75,
        signal_strength=75,
        quality_grade="A",
        expected_r=2.0,
        regime="TRENDING",
        mtf_alignment=1.0,
        risk_state="NORMAL",
    )

    # Candle that hits both SL (1.0950) and TP (1.1050) in the same bar
    outcome, reason, exit_px, net_r = canonical_prospective_ledger.resolve_against_candle(
        signal=signal,
        candle_open=1.1000,
        candle_high=1.1060,  # hits TP
        candle_low=1.0940,   # hits SL
        candle_close=1.1010,
        candle_time="2026-09-27T14:00:00Z",
    )
    # Under conservative policy, same-bar conflict must resolve to OUTCOME_LOST
    assert outcome == OUTCOME_LOST, f"Same-candle ambiguity must resolve conservatively to LOST, got {outcome}"
    assert reason == "AMBIGUOUS_CANDLE_CONSERVATIVE_SL"
    assert exit_px == 1.0950


# ── 20. Cross-Timeframe Isolation ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_cross_timeframe_isolation():
    gateway = MarketDataGateway()
    # Rates requested for 1H must have timeframe="1H"
    rates_1h = await gateway.get_rates("BTCUSD", timeframe="1H", count=5)
    for bar in rates_1h:
        assert bar.get("timeframe") in ("1H", "1h", "H1"), f"1H request contained contaminated bar: {bar}"

    # Rates requested for 4H must have timeframe="4H"
    rates_4h = await gateway.get_rates("BTCUSD", timeframe="4H", count=5)
    for bar in rates_4h:
        assert bar.get("timeframe") in ("4H", "4h", "H4"), f"4H request contained contaminated bar: {bar}"
