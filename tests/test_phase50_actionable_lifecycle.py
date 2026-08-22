"""
Phase 50 — Comprehensive Test Suite for Actionable Trade Timing, Signal Revalidation & Position Lifecycle.

Tests:
- Dynamic Entry & Holding Windows (Tests A–E)
- Pre-Entry Revalidation & Comparison Outcomes (Tests F–L)
- Anti-Whipsaw Hysteresis & Signal Versioning Lineage (Tests M–P)
- Actionable State Machine & Human Actions (Tests Q–T)
- Offline Gap Recovery & Replay Resolution (Tests U–Y)
- REST API Endpoints & Authoritative Server Countdown (Tests Z–AD)
- Phase 49 Non-Regression & Equivalence (Test AE)
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.core.market_clock import market_clock
from app.decision.revalidation_engine import revalidation_engine, RevalidationEngine
from app.decision.actionable_signal_engine import actionable_signal_engine
from app.runtime.offline_gap_recovery import offline_gap_recovery_engine


# ── TEST GROUP 1: TIMING & DYNAMIC ENVELOPES (TESTS A–E) ──────────────────────

def test_a_timing_contract_utc_ist():
    """Verify UTC internal representation and exact IST formatting."""
    utc_time = datetime(2026, 8, 21, 12, 30, 0, tzinfo=timezone.utc)
    ist_str = market_clock.format_ist(utc_time)
    assert "Friday" in ist_str
    assert "21 August 2026" in ist_str
    assert "06:00 PM IST" in ist_str


def test_b_dynamic_entry_windows_timeframe_scaling():
    """Verify entry windows dynamically adapt based on timeframe (15M, 1H, 4H, 1D)."""
    target = datetime(2026, 8, 21, 14, 0, 0, tzinfo=timezone.utc)

    w_15m = market_clock.compute_entry_window(target, timeframe="15M")
    assert w_15m["lead_minutes"] == 5
    assert w_15m["lag_minutes"] == 5

    w_1h = market_clock.compute_entry_window(target, timeframe="1H")
    assert w_1h["lead_minutes"] == 15
    assert w_1h["lag_minutes"] == 15

    w_4h = market_clock.compute_entry_window(target, timeframe="4H")
    assert w_4h["lead_minutes"] == 30
    assert w_4h["lag_minutes"] == 30

    w_1d = market_clock.compute_entry_window(target, timeframe="1D")
    assert w_1d["lead_minutes"] == 60
    assert w_1d["lag_minutes"] == 60


def test_c_dynamic_entry_windows_volatility_scaling():
    """Verify high volatility expands the entry window and low volatility contracts it."""
    target = datetime(2026, 8, 21, 14, 0, 0, tzinfo=timezone.utc)

    # Base 1H has 15m lead/lag
    w_high_vol = market_clock.compute_entry_window(target, timeframe="1H", volatility_pct=1.4)
    assert w_high_vol["lead_minutes"] == int(15 * 1.4)  # 21 mins

    w_low_vol = market_clock.compute_entry_window(target, timeframe="1H", volatility_pct=0.8)
    assert w_low_vol["lead_minutes"] == int(15 * 0.8)  # 12 mins


def test_d_dynamic_holding_envelopes():
    """Verify holding envelopes scale across timeframes and strategies."""
    h_1h = market_clock.compute_holding_window(timeframe="1H", strategy_type="INTRADAY")
    assert h_1h["expected_hold_min_hours"] == 2.0
    assert h_1h["expected_hold_max_hours"] == 4.0
    assert h_1h["maximum_hold_hours"] == 6.0

    h_4h = market_clock.compute_holding_window(timeframe="4H", strategy_type="SWING")
    assert h_4h["expected_hold_min_hours"] >= 8.0
    assert h_4h["maximum_hold_hours"] >= 48.0


def test_e_authoritative_countdown():
    """Verify backend authoritative countdown calculation."""
    now = datetime(2026, 8, 21, 10, 0, 0, tzinfo=timezone.utc)
    target = datetime(2026, 8, 21, 10, 14, 25, tzinfo=timezone.utc)

    cd = market_clock.compute_countdown(target, current_utc=now)
    assert cd["seconds_remaining"] == 865
    assert cd["is_passed"] is False
    assert cd["countdown_formatted"] == "00:14:25"
    assert cd["direction_label"] == "remaining"


# ── TEST GROUP 2: REVALIDATION & ANTI-WHIPSAW HYSTERESIS (TESTS F–L) ──────────

def test_f_revalidation_signal_strengthened():
    """Verify confidence increase >= 0.03 yields SIGNAL_STRENGTHENED."""
    prev = {
        "signal_id": "SIG-EURUSD-001",
        "version": 1,
        "direction": "BUY",
        "confidence": 0.65,
        "consensus_score": 0.70,
        "market_regime": "TRENDING_BULL",
    }
    curr = {
        "direction": "BUY",
        "confidence": 0.72,
        "consensus_score": 0.75,
        "market_regime": "TRENDING_BULL",
    }
    res = revalidation_engine.compare_and_revalidate(prev, curr)
    assert res["revalidation_status"] == "SIGNAL_STRENGTHENED"
    assert res["confidence_delta"] == 0.07
    assert res["version"] == 2
    assert "Confidence increased" in res["change_reason_text"]


def test_g_revalidation_signal_weakened():
    """Verify confidence decrease <= -0.03 yields SIGNAL_WEAKENED."""
    prev = {
        "signal_id": "SIG-EURUSD-001",
        "version": 1,
        "direction": "BUY",
        "confidence": 0.75,
        "consensus_score": 0.75,
        "market_regime": "TRENDING_BULL",
    }
    curr = {
        "direction": "BUY",
        "confidence": 0.68,
        "consensus_score": 0.70,
        "market_regime": "TRENDING_BULL",
    }
    res = revalidation_engine.compare_and_revalidate(prev, curr)
    assert res["revalidation_status"] == "SIGNAL_WEAKENED"
    assert res["confidence_delta"] == -0.07
    assert "Confidence softened" in res["change_reason_text"]


def test_h_revalidation_signal_unchanged():
    """Verify confidence delta within +-0.03 yields SIGNAL_UNCHANGED."""
    prev = {
        "signal_id": "SIG-EURUSD-001",
        "version": 1,
        "direction": "BUY",
        "confidence": 0.70,
        "consensus_score": 0.70,
        "market_regime": "TRENDING_BULL",
    }
    curr = {
        "direction": "BUY",
        "confidence": 0.71,
        "consensus_score": 0.70,
        "market_regime": "TRENDING_BULL",
    }
    res = revalidation_engine.compare_and_revalidate(prev, curr)
    assert res["revalidation_status"] == "SIGNAL_UNCHANGED"


def test_i_revalidation_signal_changed_with_strong_evidence():
    """Verify reversal with strong consensus (>=0.70) and confidence (>=0.65) triggers SIGNAL_CHANGED."""
    prev = {
        "signal_id": "SIG-EURUSD-001",
        "version": 1,
        "direction": "BUY",
        "confidence": 0.68,
        "consensus_score": 0.70,
        "market_regime": "TRENDING_BULL",
    }
    curr = {
        "direction": "SELL",
        "confidence": 0.75,
        "consensus_score": 0.80,
        "market_regime": "TRENDING_BEAR",
    }
    res = revalidation_engine.compare_and_revalidate(prev, curr)
    assert res["revalidation_status"] == "SIGNAL_CHANGED"
    assert res["direction"] == "SELL"
    assert "Direction reversed from BUY to SELL" in res["change_reason_text"]


def test_j_anti_whipsaw_hysteresis_rejection():
    """Verify reversal with insufficient consensus (<0.70) is rejected to fail-closed NO_TRADE."""
    prev = {
        "signal_id": "SIG-EURUSD-001",
        "version": 1,
        "direction": "BUY",
        "confidence": 0.68,
        "consensus_score": 0.70,
        "market_regime": "TRENDING_BULL",
    }
    curr = {
        "direction": "SELL",
        "confidence": 0.55,
        "consensus_score": 0.52,  # Too weak for reversal
        "market_regime": "CHOPPY",
    }
    res = revalidation_engine.compare_and_revalidate(prev, curr)
    assert res["revalidation_status"] == "SIGNAL_INVALIDATED"
    assert res["actionable_status"] == "NO_TRADE"
    assert res["no_trade_reason"] == "MODEL_DISAGREEMENT"


def test_k_price_stop_loss_invalidation():
    """Verify signal is invalidated if live price has already breached initial stop loss."""
    prev = {
        "signal_id": "SIG-EURUSD-001",
        "version": 1,
        "direction": "BUY",
        "entry_price": 1.0850,
        "stop_loss": 1.0820,
        "confidence": 0.70,
    }
    curr = {
        "direction": "BUY",
        "confidence": 0.70,
    }
    # Live market price 1.0815 has breached SL (1.0820)
    res = revalidation_engine.compare_and_revalidate(
        prev, curr, current_market={"price": 1.0815}
    )
    assert res["revalidation_status"] == "SIGNAL_INVALIDATED"
    assert res["no_trade_reason"] == "PRICE_HIT_STOP_LOSS"


def test_l_event_risk_blocking():
    """Verify HIGH event risk blocks trade execution with EVENT_BLOCKED status."""
    prev = {
        "signal_id": "SIG-USDJPY-001",
        "version": 1,
        "direction": "BUY",
        "confidence": 0.75,
    }
    curr = {
        "direction": "BUY",
        "confidence": 0.75,
        "event_risk": "HIGH",
    }
    res = revalidation_engine.compare_and_revalidate(prev, curr)
    assert res["revalidation_status"] == "EVENT_BLOCKED"
    assert res["actionable_status"] == "NO_TRADE"
    assert res["no_trade_reason"] == "HIGH_EVENT_RISK"


# ── TEST GROUP 3: STATE MACHINE & SIGNAL LIFECYCLE (TESTS M–P) ────────────────

def test_m_state_machine_watch_to_enter_now_to_expired():
    """Verify actionable state transitions: WATCH -> ENTER_NOW -> EXPIRED."""
    target = datetime(2026, 8, 21, 14, 0, 0, tzinfo=timezone.utc)
    forecast = {
        "asset": "EURUSD",
        "timeframe": "1H",
        "direction": "BUY",
        "confidence": 0.75,
        "consensus_score": 0.80,
        "is_trade_qualified": True,
        "entry_price": 1.0850,
        "stop_loss": 1.0820,
        "take_profit": 1.0910,
        "risk_reward": 2.0,
    }

    # 1. 30 minutes before target: before entry window start (-15m) -> WATCH / WAIT
    t_early = target - timedelta(minutes=30)
    opp_early = actionable_signal_engine.create_actionable_opportunity(
        forecast, target_utc=target, now_utc=t_early
    )
    assert opp_early["status"] == "WATCH"
    assert opp_early["primary_action"] == "WAIT"

    # 2. 5 minutes before target: inside entry window -> ENTER_NOW / ENTER NOW
    t_inside = target - timedelta(minutes=5)
    opp_inside = actionable_signal_engine.create_actionable_opportunity(
        forecast, target_utc=target, now_utc=t_inside
    )
    assert opp_inside["status"] == "ENTER_NOW"
    assert opp_inside["primary_action"] == "ENTER NOW"

    # 3. 20 minutes after target: past entry window end (+15m) -> EXPIRED
    t_late = target + timedelta(minutes=20)
    opp_late = actionable_signal_engine.create_actionable_opportunity(
        forecast, target_utc=target, now_utc=t_late
    )
    assert opp_late["status"] == "EXPIRED"
    assert opp_late["primary_action"] == "EXPIRED"


def test_n_signal_versioning_and_parent_lineage():
    """Verify version tracking v1 -> v2 -> v3 and parent_signal_id preservation."""
    initial_fc = {
        "asset": "GBPUSD",
        "timeframe": "1H",
        "direction": "BUY",
        "confidence": 0.68,
        "consensus_score": 0.70,
        "is_trade_qualified": True,
    }
    opp_v1 = actionable_signal_engine.create_actionable_opportunity(initial_fc)
    sig_id = opp_v1["signal_id"]
    assert opp_v1["version"] == 1
    assert opp_v1["parent_signal_id"] == sig_id

    # Revalidate #1: Strengthened
    fc_v2 = dict(initial_fc)
    fc_v2["confidence"] = 0.76
    opp_v2 = actionable_signal_engine.revalidate_opportunity(sig_id, fc_v2)
    assert opp_v2["version"] == 2
    assert opp_v2["parent_signal_id"] == sig_id
    assert opp_v2["revalidation_count"] == 1

    # Check evolution timeline
    history = actionable_signal_engine.get_signal_evolution(sig_id)
    assert len(history) >= 2


def test_o_zero_trust_no_trade_gating():
    """Verify setups with consensus < 0.65 are gated as NO_TRADE."""
    low_consensus_fc = {
        "asset": "USDJPY",
        "timeframe": "1H",
        "direction": "BUY",
        "confidence": 0.70,
        "consensus_score": 0.55,  # Gated by consensus threshold
        "is_trade_qualified": False,
        "rejection_reason": "CONSENSUS_BELOW_0.65",
    }
    opp = actionable_signal_engine.create_actionable_opportunity(low_consensus_fc)
    assert opp["status"] == "NO_TRADE"
    assert opp["primary_action"] == "NO TRADE"
    assert opp["no_trade_reason"] == "CONSENSUS_BELOW_0.65"


def test_p_stale_data_fails_closed():
    """Verify DATA_STALE status halts actionable progression."""
    stale_fc = {
        "asset": "BTCUSD",
        "timeframe": "1H",
        "direction": "BUY",
        "confidence": 0.85,
        "consensus_score": 0.85,
        "data_freshness_status": "DATA_STALE",
    }
    opp = actionable_signal_engine.create_actionable_opportunity(stale_fc)
    assert opp["status"] == "DATA_STALE"
    assert opp["primary_action"] == "NO TRADE"
    assert opp["data_freshness_status"] == "DATA_STALE"


# ── TEST GROUP 4: OFFLINE GAP RECOVERY & CANDLE REPLAY (TESTS Q–U) ─────────────

def test_q_offline_gap_detection():
    """Verify engine correctly inspects historical SQLite tables for gaps."""
    res = offline_gap_recovery_engine.detect_offline_gaps(["EURUSD", "BTCUSD"])
    assert res["status"] in ["CHECKED", "NO_DATABASE"]
    assert "EURUSD" in res.get("gaps", {})


def test_r_candle_replay_tp_hit_with_mfe_mae():
    """Verify candle replay detects TP_HIT, calculates Gross/Net R, MFE, MAE, and friction."""
    trade = {
        "trade_id": "PT-001",
        "asset": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.0850,
        "stop_loss": 1.0800,   # Risk = 50 pips (0.0050)
        "take_profit": 1.0950, # TP = 100 pips (+2.0R)
        "status": "PAPER_OPEN",
    }
    candles = [
        {"open": 1.0850, "high": 1.0870, "low": 1.0840, "close": 1.0865, "timestamp": "2026-08-21T01:00:00Z"},
        {"open": 1.0865, "high": 1.0900, "low": 1.0855, "close": 1.0890, "timestamp": "2026-08-21T02:00:00Z"},
        {"open": 1.0890, "high": 1.0960, "low": 1.0880, "close": 1.0955, "timestamp": "2026-08-21T03:00:00Z"},  # TP Hit here
    ]
    resolved = offline_gap_recovery_engine.resolve_trade_with_mfe_mae(trade, candles)
    assert resolved is not None
    assert resolved["status"] == "TP_HIT"
    assert resolved["gross_r"] == 2.0
    assert resolved["net_r"] > 1.8  # Deducted friction
    assert resolved["mfe_r"] >= 2.0
    assert resolved["holding_bars"] == 3


def test_s_candle_replay_sl_hit_with_mfe_mae():
    """Verify candle replay detects SL_HIT, calculates -1.0R Gross, and friction."""
    trade = {
        "trade_id": "PT-002",
        "asset": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.0850,
        "stop_loss": 1.0800,
        "take_profit": 1.0950,
        "status": "PAPER_OPEN",
    }
    candles = [
        {"open": 1.0850, "high": 1.0860, "low": 1.0830, "close": 1.0835, "timestamp": "2026-08-21T01:00:00Z"},
        {"open": 1.0835, "high": 1.0840, "low": 1.0790, "close": 1.0795, "timestamp": "2026-08-21T02:00:00Z"},  # SL Hit here
    ]
    resolved = offline_gap_recovery_engine.resolve_trade_with_mfe_mae(trade, candles)
    assert resolved is not None
    assert resolved["status"] == "SL_HIT"
    assert resolved["gross_r"] == -1.0
    assert resolved["net_r"] < -1.0  # Slippage/spread friction added to loss
    assert resolved["holding_bars"] == 2


def test_t_candle_replay_intra_candle_ambiguity():
    """Verify single candle breaching both TP and SL is flagged as AMBIGUOUS."""
    trade = {
        "trade_id": "PT-003",
        "asset": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.0850,
        "stop_loss": 1.0800,
        "take_profit": 1.0950,
        "status": "PAPER_OPEN",
    }
    # Extreme volatility bar crosses both
    candles = [
        {"open": 1.0850, "high": 1.0980, "low": 1.0780, "close": 1.0860, "timestamp": "2026-08-21T01:00:00Z"}
    ]
    resolved = offline_gap_recovery_engine.resolve_trade_with_mfe_mae(trade, candles)
    assert resolved is not None
    assert resolved["status"] == "AMBIGUOUS"


def test_u_candle_replay_time_exit():
    """Verify trade exceeding time without hitting TP or SL resolves as TIME_EXIT."""
    trade = {
        "trade_id": "PT-004",
        "asset": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.0850,
        "stop_loss": 1.0800,
        "take_profit": 1.0950,
        "status": "PAPER_OPEN",
    }
    candles = [
        {"open": 1.0850, "high": 1.0880, "low": 1.0840, "close": 1.0875, "timestamp": "2026-08-21T01:00:00Z"},
        {"open": 1.0875, "high": 1.0890, "low": 1.0860, "close": 1.0880, "timestamp": "2026-08-21T02:00:00Z"},
    ]
    resolved = offline_gap_recovery_engine.resolve_trade_with_mfe_mae(trade, candles, max_hold_hours=2.0)
    assert resolved is not None
    assert resolved["status"] == "TIME_EXIT"
    assert resolved["gross_r"] > 0.0


# ── TEST GROUP 5: REST API ENDPOINTS (TESTS V–Z) ──────────────────────────────

@pytest.fixture
def client():
    return TestClient(app)


def test_v_api_get_actionable_signals(client):
    """Verify GET /api/v1/signals/actionable returns structured opportunities."""
    res = client.get("/api/v1/signals/actionable?include_expired=true")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "server_time_ist" in data
    assert isinstance(data["actionable_opportunities"], list)


def test_w_api_get_next_setup(client):
    """Verify GET /api/v1/signals/next-setup returns single actionable setup or null state."""
    res = client.get("/api/v1/signals/next-setup")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "has_setup" in data
    assert "server_time_ist" in data


def test_x_api_revalidate_signal(client):
    """Verify POST /api/v1/signals/{signal_id}/revalidate re-evaluates setup."""
    # Pre-seed an opportunity in engine
    opp = actionable_signal_engine.create_actionable_opportunity({
        "asset": "EURUSD",
        "timeframe": "1H",
        "direction": "BUY",
        "confidence": 0.70,
        "consensus_score": 0.75,
        "is_trade_qualified": True,
        "entry_price": 1.0850,
        "stop_loss": 1.0820,
        "take_profit": 1.0910,
    })
    sig_id = opp["signal_id"]

    res = client.post(f"/api/v1/signals/{sig_id}/revalidate")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "revalidation_outcome" in data
    assert "updated_signal" in data


def test_y_api_signal_evolution(client):
    """Verify GET /api/v1/signals/{signal_id}/evolution returns lineage timeline."""
    opp = actionable_signal_engine.create_actionable_opportunity({
        "asset": "GBPUSD",
        "timeframe": "1H",
        "direction": "BUY",
        "confidence": 0.72,
        "consensus_score": 0.75,
        "is_trade_qualified": True,
    })
    sig_id = opp["signal_id"]

    res = client.get(f"/api/v1/signals/{sig_id}/evolution")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "evolution_timeline" in data


def test_z_api_countdown(client):
    """Verify GET /api/v1/signals/countdown returns server clock and timing."""
    target_iso = (datetime.now(timezone.utc) + timedelta(minutes=45)).isoformat()
    res = client.get(f"/api/v1/signals/countdown?target_utc={target_iso}")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "countdown" in data
    assert data["countdown"]["seconds_remaining"] > 0


# ── TEST GROUP 6: PHASE 49 NON-REGRESSION (TESTS AA–AE) ───────────────────────

@pytest.mark.asyncio
async def test_aa_phase49_restart_equivalence_non_regression():
    """Verify Phase 49 restart equivalence constraints remain strictly satisfied."""
    from tests.test_phase49_restart_equivalence import (
        test_market_clock_ist_formatting,
        test_market_clock_staleness,
        test_target_time_expiration,
    )
    await test_market_clock_ist_formatting()
    await test_market_clock_staleness()
    await test_target_time_expiration()

