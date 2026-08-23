"""
tests/test_single_source_of_truth_pipeline.py
=============================================
Comprehensive test suite verifying:
1. Single Source of Truth Pipeline Architecture.
2. Market Session & Weekend Gating (Forex, Metals, Indices vs Crypto 24/7).
3. Forecast vs Actionable Trade Signal vs Paper Trade Separation.
4. Offline Trade Reconciliation & Application Restart Lifecycle.
5. End-to-End API endpoint parity & Zero-Trust Governance.
"""

import pytest
import sqlite3
import os
from datetime import datetime, timezone, timedelta

from app.core.market_session import market_session_service, AssetTradingCalendar
from app.market_data.registry import asset_registry
from app.analytics.tomorrow_forecast_engine import tomorrow_forecast_engine
from app.runtime.live_forecast_scheduler import live_forecast_scheduler
from app.runtime.trade_reconciliation_service import trade_reconciliation_service
from app.analytics.shadow_ledger_engine import shadow_ledger_engine, ASSET_COST_PROFILES


# ── 1. Market Session & Weekend Gating Tests ─────────────────────────────────

def test_crypto_market_is_always_open():
    """Crypto (BTCUSD, ETHUSD) must be open 24/7 across any day/time."""
    # Test Saturday UTC
    sat_dt = datetime(2026, 8, 22, 14, 0, 0, tzinfo=timezone.utc)
    btc_status = market_session_service.get_market_status("BTCUSD", sat_dt)
    eth_status = market_session_service.get_market_status("ETHUSD", sat_dt)

    assert btc_status["is_market_open"] is True
    assert eth_status["is_market_open"] is True
    assert btc_status["status_label"] == "OPEN"
    assert btc_status["current_session"] == "24/7_CONTINUOUS"


def test_forex_is_closed_on_saturday():
    """Forex pairs (EURUSD, GBPUSD, USDJPY, AUDUSD) must be closed on Saturday."""
    sat_dt = datetime(2026, 8, 22, 12, 0, 0, tzinfo=timezone.utc)
    for pair in ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]:
        status = market_session_service.get_market_status(pair, sat_dt)
        assert status["is_market_open"] is False
        assert status["status_label"] == "CLOSED"
        assert status["reason"] == "WEEKEND_SATURDAY"
        assert status["next_open_utc"] is not None


def test_forex_is_closed_on_sunday_premarket():
    """Forex pairs must remain closed on Sunday before 22:00 UTC."""
    sun_early = datetime(2026, 8, 23, 10, 0, 0, tzinfo=timezone.utc)
    status = market_session_service.get_market_status("EURUSD", sun_early)
    assert status["is_market_open"] is False
    assert status["reason"] == "WEEKEND_SUNDAY_PRE_MARKET"


def test_forex_opens_on_sunday_2200_utc():
    """Forex pairs must be OPEN on Sunday after 22:00 UTC (Sydney open)."""
    sun_late = datetime(2026, 8, 23, 22, 30, 0, tzinfo=timezone.utc)
    status = market_session_service.get_market_status("EURUSD", sun_late)
    assert status["is_market_open"] is True
    assert status["status_label"] == "OPEN"
    assert status["current_session"] == "SYDNEY_OPEN"


def test_forex_is_open_midweek():
    """Forex pairs must be OPEN on Wednesday during London session."""
    wed_dt = datetime(2026, 8, 26, 10, 30, 0, tzinfo=timezone.utc)
    status = market_session_service.get_market_status("EURUSD", wed_dt)
    assert status["is_market_open"] is True
    assert status["status_label"] == "OPEN"
    assert status["current_session"] == "LONDON_SESSION"


def test_metals_and_indices_closed_on_weekends():
    """Gold (XAUUSD) and Indices (NAS100, SPX500) must be closed on weekends."""
    sat_dt = datetime(2026, 8, 22, 15, 0, 0, tzinfo=timezone.utc)
    gold = market_session_service.get_market_status("XAUUSD", sat_dt)
    nas = market_session_service.get_market_status("NAS100", sat_dt)
    spx = market_session_service.get_market_status("SPX500", sat_dt)

    assert gold["is_market_open"] is False
    assert nas["is_market_open"] is False
    assert spx["is_market_open"] is False


def test_asset_registry_integration():
    """AssetRegistry.is_market_open and get_market_status must delegate to MarketSessionService."""
    sat_dt = datetime(2026, 8, 22, 12, 0, 0, tzinfo=timezone.utc)
    assert asset_registry.is_market_open("BTCUSD", sat_dt) is True
    assert asset_registry.is_market_open("EURUSD", sat_dt) is False

    status = asset_registry.get_market_status("EURUSD", sat_dt)
    assert status["symbol"] == "EURUSD"
    assert status["is_market_open"] is False


def test_all_market_statuses_returns_all_9_assets():
    """get_all_market_statuses must return statuses for all 9 universe assets."""
    statuses = market_session_service.get_all_market_statuses()
    assert len(statuses) == 9
    symbols = [s["symbol"] for s in statuses]
    for expected in ["BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "NAS100", "SPX500"]:
        assert expected in symbols


# ── 2. Forecast vs Signal Separation & Gating Tests ─────────────────────────

@pytest.mark.asyncio
async def test_tomorrow_forecast_gates_closed_markets():
    """When market is closed (e.g. Saturday), tomorrow forecast produces FORECAST_ONLY and NO_TRADE."""
    sat_dt = datetime(2026, 8, 22, 14, 0, 0, tzinfo=timezone.utc)
    res = await tomorrow_forecast_engine.generate_tomorrow_forecasts(data_cutoff=sat_dt)

    assert res["summary"]["total_assets"] == 9
    eur_fc = next(f for f in res["forecasts"] if f["asset"] == "EURUSD")
    
    # Forecast exists
    assert eur_fc["direction"] in ["BUY", "SELL", "NEUTRAL"]
    assert eur_fc["confidence"] > 0
    # But Trade Signal is gated
    assert eur_fc["is_market_open"] is False
    assert eur_fc["is_trade_signal_qualified"] is False
    assert eur_fc["trade_signal_decision"] == "NO_TRADE"
    assert eur_fc["trade_disqualification_reason"] == "MARKET_CLOSED"
    assert "FORECAST_ONLY" in eur_fc["status"]


@pytest.mark.asyncio
async def test_tomorrow_forecast_allows_crypto_trade_signals():
    """Crypto (BTCUSD) is open on weekends, so it can qualify if confidence criteria pass."""
    sat_dt = datetime(2026, 8, 22, 14, 0, 0, tzinfo=timezone.utc)
    res = await tomorrow_forecast_engine.generate_tomorrow_forecasts(data_cutoff=sat_dt)
    btc_fc = next(f for f in res["forecasts"] if f["asset"] == "BTCUSD")

    assert btc_fc["is_market_open"] is True
    # If not qualified, reason should be consensus/RR/event, NOT MARKET_CLOSED
    if not btc_fc["is_trade_signal_qualified"]:
        assert btc_fc["trade_disqualification_reason"] != "MARKET_CLOSED"


def test_live_forecast_scheduler_gates_closed_markets():
    """live_forecast_scheduler must gate EURUSD with MARKET_CLOSED when market is closed."""
    # Mock candle on Saturday
    sat_candle = {
        "timestamp": "2026-08-22 14:00:00",
        "close": 1.0850,
    }
    pred = live_forecast_scheduler.evaluate_multi_model_forecast("EURUSD", sat_candle)
    assert pred["is_trade_qualified"] is False
    assert pred["rejection_reason"] == "MARKET_CLOSED"
    assert pred["is_market_open"] is False


# ── 3. Offline Trade Reconciliation & Candle Replay Tests ───────────────────

def test_trade_reconciliation_detects_take_profit():
    """Replay candles must detect Take Profit when price reaches or crosses TP."""
    trade = {
        "trade_id": "TEST_TP_01",
        "asset": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.0800,
        "stop_loss": 1.0750,
        "take_profit": 1.0900,
        "status": "PAPER_OPEN",
        "entry_time": "2026-08-20T10:00:00+00:00",
    }
    candles = [
        {"open": 1.0805, "high": 1.0840, "low": 1.0790, "close": 1.0830, "timestamp": "2026-08-20T11:00:00"},
        {"open": 1.0830, "high": 1.0920, "low": 1.0820, "close": 1.0910, "timestamp": "2026-08-20T12:00:00"},
    ]

    res = trade_reconciliation_service.replay_trade_lifecycle(trade, candles)
    assert res is not None
    assert res["status"] == "TP_HIT"
    assert res["exit_price"] == 1.0900
    assert res["gross_r"] == 2.0
    assert res["net_r"] > 1.90  # Gross 2.0 - costs
    assert res["mfe_r"] > 2.0


def test_trade_reconciliation_detects_stop_loss():
    """Replay candles must detect Stop Loss when price reaches or breaches SL."""
    trade = {
        "trade_id": "TEST_SL_01",
        "asset": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.0800,
        "stop_loss": 1.0750,
        "take_profit": 1.0900,
        "status": "PAPER_OPEN",
        "entry_time": "2026-08-20T10:00:00+00:00",
    }
    candles = [
        {"open": 1.0790, "high": 1.0810, "low": 1.0740, "close": 1.0745, "timestamp": "2026-08-20T11:00:00"},
    ]

    res = trade_reconciliation_service.replay_trade_lifecycle(trade, candles)
    assert res is not None
    assert res["status"] == "SL_HIT"
    assert res["exit_price"] == 1.0750
    assert res["gross_r"] == -1.0
    assert res["net_r"] < -1.0  # -1.0 - costs
    assert res["mae_r"] >= 1.0


def test_trade_reconciliation_detects_time_exit():
    """Replay candles must expire trade via TIME_EXIT when max holding duration is exceeded."""
    trade = {
        "trade_id": "TEST_TIME_01",
        "asset": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.0800,
        "stop_loss": 1.0750,
        "take_profit": 1.0900,
        "status": "PAPER_OPEN",
        "entry_time": "2026-08-20T10:00:00+00:00",
    }
    # 7 candles of chop within SL/TP bounds (max_hold_hours = 6.0)
    candles = [
        {"open": 1.0800, "high": 1.0820, "low": 1.0780, "close": 1.0810, "timestamp": f"2026-08-20T{11+i:02d}:00:00"}
        for i in range(7)
    ]

    res = trade_reconciliation_service.replay_trade_lifecycle(trade, candles, max_hold_hours=6.0)
    assert res is not None
    assert res["status"] == "TIME_EXIT"
    assert res["exit_price"] == 1.0810
    assert res["holding_bars"] == 7


def test_trade_reconciliation_handles_ambiguous_candle_path():
    """If single candle breaches BOTH TP and SL, outcome is deterministically marked AMBIGUOUS_CANDLE_PATH."""
    trade = {
        "trade_id": "TEST_AMBIGUOUS_01",
        "asset": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.0800,
        "stop_loss": 1.0750,
        "take_profit": 1.0900,
        "status": "PAPER_OPEN",
        "entry_time": "2026-08-20T10:00:00+00:00",
    }
    candles = [
        {"open": 1.0800, "high": 1.0950, "low": 1.0700, "close": 1.0820, "timestamp": "2026-08-20T11:00:00"},
    ]

    res = trade_reconciliation_service.replay_trade_lifecycle(trade, candles)
    assert res is not None
    assert res["status"] == "AMBIGUOUS_CANDLE_PATH"
    assert res["gross_r"] == 0.0
    assert res["net_r"] <= 0.0  # Friction only


def test_bootstrap_sequence_generates_comprehensive_report():
    """execute_bootstrap_sequence must generate a complete system readiness report."""
    report = trade_reconciliation_service.execute_bootstrap_sequence()

    assert report["system_status"] == "SYSTEM_READY"
    assert "market_summary" in report
    assert report["market_summary"]["total_monitored_assets"] == 9
    assert "trade_recovery" in report
    assert report["zero_trust_policy"] == "FROZEN_ENFORCED (79a4f8e12b79310d)"
    assert report["real_money_execution"] == "STRICTLY_DISABLED"


# ── 4. End-to-End Stop & Restart Simulation ──────────────────────────────────

def test_stop_restart_lifecycle_reconciles_open_paper_trade():
    """
    Simulates the exact user story:
    1. Project runs -> creates open paper trade.
    2. Project closes.
    3. User restarts hours later.
    4. Bootstrap reconciles trade against closed candle and marks TP_HIT.
    """
    # 1. Spawn a paper trade in shadow ledger
    trade = shadow_ledger_engine.spawn_paper_trade(
        prediction_id="P-TEST-CYCLE-1",
        asset="BTCUSD",
        direction="BUY",
        entry_price=60000.0,
        stop_loss=58000.0,
        take_profit=64000.0,
        risk_reward=2.0,
        confidence=0.75,
    )
    trade_id = trade["trade_id"]
    assert trade["status"] == "PAPER_OPEN"

    # 2. Simulate offline period and missed closed candles reaching take profit
    future_candles = [
        {"open": 60100.0, "high": 61500.0, "low": 59900.0, "close": 61200.0, "timestamp": "2026-08-23T12:00:00"},
        {"open": 61200.0, "high": 64500.0, "low": 61000.0, "close": 64200.0, "timestamp": "2026-08-23T13:00:00"},
    ]

    # 3. Simulate Restart -> TradeReconciliationService evaluates trade
    resolved = trade_reconciliation_service.replay_trade_lifecycle(trade, future_candles)
    assert resolved is not None
    assert resolved["status"] == "TP_HIT"
    assert resolved["exit_price"] == 64000.0
    assert resolved["gross_r"] >= 1.90
    assert resolved["net_r"] > 1.85

    # 4. Update shadow ledger manually
    shadow_ledger_engine.resolve_trade_manual(
        trade_id=trade_id,
        exit_price=resolved["exit_price"],
        exit_time=resolved["exit_time"],
        status=resolved["status"],
        gross_r=resolved["gross_r"],
        net_r=resolved["net_r"],
    )

    # 5. Verify trade is no longer in open list
    open_trades = shadow_ledger_engine.get_open_paper_trades()
    assert not any(t["trade_id"] == trade_id for t in open_trades)


# ── 5. Zero-Trust & Configuration Immutability Tests ─────────────────────────

def test_frozen_configuration_hash_integrity():
    """Verifies that CONFIG_HASH is frozen and preserved as 79a4f8e12b79310d."""
    EXPECTED_CONFIG_HASH = "79a4f8e12b79310d"
    from app.decision.canonical_decision_engine import canonical_decision_engine
    from app.analytics.signal_truth_ledger import signal_truth_ledger
    assert canonical_decision_engine.config_hash == EXPECTED_CONFIG_HASH
    assert signal_truth_ledger.CONFIG_HASH == EXPECTED_CONFIG_HASH


def test_real_money_execution_strictly_disabled():
    """Verifies that live broker execution is hard-disabled across all pathways."""
    from app.config.settings import get_settings
    settings = get_settings()
    assert settings.EXECUTION_MODE in ("PAPER", "DEMO", "BACKTEST", "VALIDATION")
    assert settings.EXECUTION_MODE != "REAL_MONEY"


# ── 6. Additional Architecture & API Parity Tests ────────────────────────────

@pytest.mark.asyncio
async def test_market_status_api_endpoint():
    """Verifies GET /api/v1/market/status endpoint returns valid data."""
    from app.api.v1.market import get_all_market_status, get_symbol_market_status
    res = await get_all_market_status()
    assert res["success"] is True
    assert res["total_assets"] == 9
    assert len(res["statuses"]) == 9

    sym_res = await get_symbol_market_status("BTCUSD")
    assert sym_res["success"] is True
    assert sym_res["data"]["is_market_open"] is True


def test_bootstrap_status_api_endpoint():
    """Verifies system intelligence bootstrap endpoints return valid structure."""
    from app.api.v1.system_intelligence_routes import execute_system_bootstrap, get_system_bootstrap_status
    res = execute_system_bootstrap()
    assert res["success"] is True
    assert res["report"]["system_status"] == "SYSTEM_READY"

    status_res = get_system_bootstrap_status()
    assert status_res["success"] is True
    assert status_res["report"]["market_summary"]["total_monitored_assets"] == 9


def test_metals_daily_maintenance_break():
    """Gold (XAUUSD) has a daily break between 21:00 and 22:00 UTC."""
    wed_break = datetime(2026, 8, 26, 21, 30, 0, tzinfo=timezone.utc)
    status = market_session_service.get_market_status("XAUUSD", wed_break)
    assert status["is_market_open"] is False
    assert status["reason"] == "DAILY_MAINTENANCE_BREAK"


def test_index_cfd_settlement_break():
    """Indices (NAS100, SPX500) have a daily settlement break around 21:15-22:00 UTC."""
    wed_break = datetime(2026, 8, 26, 21, 30, 0, tzinfo=timezone.utc)
    nas_status = market_session_service.get_market_status("NAS100", wed_break)
    assert nas_status["is_market_open"] is False
    assert nas_status["reason"] == "DAILY_SETTLEMENT_BREAK"


def test_forex_friday_market_close():
    """Forex pairs close on Friday at 21:00 UTC."""
    fri_late = datetime(2026, 8, 28, 21, 15, 0, tzinfo=timezone.utc)
    status = market_session_service.get_market_status("EURUSD", fri_late)
    assert status["is_market_open"] is False
    assert status["reason"] == "WEEKEND_FRIDAY_CLOSE"


def test_offline_reconciliation_empty_candles_no_op():
    """If no subsequent closed candles exist, trade remains PAPER_OPEN and untouched."""
    trade = {
        "trade_id": "TEST_NO_CANDLE_01",
        "asset": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.0800,
        "stop_loss": 1.0750,
        "take_profit": 1.0900,
        "status": "PAPER_OPEN",
        "entry_time": "2026-08-23T10:00:00+00:00",
    }
    resolved = trade_reconciliation_service.replay_trade_lifecycle(trade, [])
    assert resolved is None

