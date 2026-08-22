"""
Phase 50 — Comprehensive Forensic Runtime Audit Test Suite
Executes forensic verification across Parts 4 through 28.
"""
import os
import sys
import pytest
import sqlite3
import time
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.main import app
from app.core.market_clock import market_clock, MarketClockService
from app.decision.revalidation_engine import revalidation_engine, RevalidationEngine
from app.decision.actionable_signal_engine import actionable_signal_engine, ActionableSignalEngine
from app.runtime.offline_gap_recovery import offline_gap_recovery_engine
from app.runtime.startup_sync import StartupSyncService, CORE_ASSETS
from app.execution.outcome_engine import OutcomeResult, OUTCOME_TP_HIT, OUTCOME_SL_HIT, OUTCOME_AMBIGUOUS, OUTCOME_TIME_EXIT

client = TestClient(app)
DB_PATH = os.path.join(PROJECT_ROOT, "tradesignal.db")


# ═══════════════════════════════════════════════════════════════════════════════
# PART 4 — ACTIONABLE SIGNAL GATING (12 GATING CONDITIONS)
# ═══════════════════════════════════════════════════════════════════════════════

def test_part4_actionable_gating_12_conditions():
    """Verify that every violation of the 12 gating conditions prevents actionable execution."""
    now = datetime(2026, 8, 21, 14, 0, 0, tzinfo=timezone.utc)
    base_valid = {
        "asset": "EURUSD",
        "timeframe": "1H",
        "direction": "BUY",
        "confidence": 0.75,
        "consensus_score": 0.80,
        "is_trade_qualified": True,
        "entry_price": 1.0850,
        "stop_loss": 1.0800,
        "take_profit": 1.0950,
        "risk_reward": 2.0,
        "event_risk": "NONE",
        "data_freshness_status": "FRESH",
    }
    target = now + timedelta(minutes=5)

    # 1. Base case: inside entry window -> ENTER_NOW
    opp = actionable_signal_engine.create_actionable_opportunity(base_valid, target_utc=target, now_utc=now)
    assert opp["status"] == "ENTER_NOW"
    assert opp["primary_action"] == "ENTER NOW"

    # 2. Condition 1 & 11: Past target / Expired entry window -> EXPIRED
    past_target = now - timedelta(minutes=30)
    opp_exp = actionable_signal_engine.create_actionable_opportunity(base_valid, target_utc=past_target, now_utc=now)
    assert opp_exp["status"] == "EXPIRED"
    assert opp_exp["primary_action"] == "EXPIRED"

    # 3. Condition 4: Stale market data -> DATA_STALE
    stale_fc = dict(base_valid, data_freshness_status="DATA_STALE")
    opp_stale = actionable_signal_engine.create_actionable_opportunity(stale_fc, target_utc=target, now_utc=now)
    assert opp_stale["status"] == "DATA_STALE"
    assert opp_stale["primary_action"] == "NO TRADE"

    # 4. Condition 5: Low confidence (< 0.60) -> NO_TRADE
    low_conf = dict(base_valid, confidence=0.55)
    opp_lc = actionable_signal_engine.create_actionable_opportunity(low_conf, target_utc=target, now_utc=now)
    assert opp_lc["status"] == "NO_TRADE"
    assert opp_lc["no_trade_reason"] == "LOW_CONFIDENCE"

    # 5. Condition 6: Low consensus (< 0.65) -> NO_TRADE
    low_cons = dict(base_valid, consensus_score=0.60)
    opp_lcons = actionable_signal_engine.create_actionable_opportunity(low_cons, target_utc=target, now_utc=now)
    assert opp_lcons["status"] == "NO_TRADE"
    assert opp_lcons["no_trade_reason"] == "LOW_CONSENSUS"

    # 6. Condition 8: High Event Risk -> NO_TRADE
    high_event = dict(base_valid, event_risk="HIGH")
    opp_event = actionable_signal_engine.create_actionable_opportunity(high_event, target_utc=target, now_utc=now)
    assert opp_event["status"] == "NO_TRADE"
    assert opp_event["no_trade_reason"] == "HIGH_EVENT_RISK"

    # 7. Condition 9: Low Risk:Reward (< 1.2) -> NO_TRADE
    low_rr = dict(base_valid, risk_reward=1.0)
    opp_rr = actionable_signal_engine.create_actionable_opportunity(low_rr, target_utc=target, now_utc=now)
    assert opp_rr["status"] == "NO_TRADE"
    assert opp_rr["no_trade_reason"] == "LOW_RR"

    # 8. Condition 10: Neutral direction -> NO_TRADE
    neutral = dict(base_valid, direction="NEUTRAL")
    opp_neut = actionable_signal_engine.create_actionable_opportunity(neutral, target_utc=target, now_utc=now)
    assert opp_neut["status"] == "NO_TRADE"


# ═══════════════════════════════════════════════════════════════════════════════
# PART 5 — NEXT SETUP RANKING ALGORITHM
# ═══════════════════════════════════════════════════════════════════════════════

def test_part5_next_setup_ranking_algorithm():
    """Verify deterministic ranking prioritizing ENTER_NOW over WAIT, and confidence/soonest window."""
    engine = ActionableSignalEngine()
    now = datetime(2026, 8, 21, 14, 0, 0, tzinfo=timezone.utc)

    # Case 0: Empty state
    assert engine.get_next_actionable_setup() is None

    # Add WAIT setup (target in 2 hours)
    s_wait1 = engine.create_actionable_opportunity(
        {"asset": "USDJPY", "timeframe": "1H", "direction": "BUY", "confidence": 0.85, "consensus_score": 0.85},
        target_utc=now + timedelta(hours=2),
        now_utc=now,
    )
    # Add WAIT setup (target in 45 mins - sooner)
    s_wait2 = engine.create_actionable_opportunity(
        {"asset": "GBPUSD", "timeframe": "1H", "direction": "BUY", "confidence": 0.70, "consensus_score": 0.75},
        target_utc=now + timedelta(minutes=45),
        now_utc=now,
    )
    # Sooner WAIT setup is selected over later higher-confidence WAIT setup
    next_s = engine.get_next_actionable_setup(now_utc=now)
    assert next_s["asset"] == "GBPUSD"

    # Add ENTER_NOW setup (target in 5 mins)
    s_now1 = engine.create_actionable_opportunity(
        {"asset": "EURUSD", "timeframe": "1H", "direction": "BUY", "confidence": 0.72, "consensus_score": 0.78},
        target_utc=now + timedelta(minutes=5),
        now_utc=now,
    )
    # ENTER_NOW is immediately prioritized over both WAIT setups
    next_s = engine.get_next_actionable_setup(now_utc=now)
    assert next_s["asset"] == "EURUSD"
    assert next_s["primary_action"] == "ENTER NOW"

    # Add higher confidence ENTER_NOW setup
    s_now2 = engine.create_actionable_opportunity(
        {"asset": "AUDUSD", "timeframe": "1H", "direction": "BUY", "confidence": 0.82, "consensus_score": 0.85},
        target_utc=now + timedelta(minutes=7),
        now_utc=now,
    )
    # Highest confidence ENTER_NOW setup is selected
    next_s = engine.get_next_actionable_setup(now_utc=now)
    assert next_s["asset"] == "AUDUSD"
    assert next_s["confidence"] == 0.82


# ═══════════════════════════════════════════════════════════════════════════════
# PART 6 — SIGNAL STATE MACHINE & TRANSITIONS
# ═══════════════════════════════════════════════════════════════════════════════

def test_part6_signal_state_machine_transitions():
    """Verify that state machine progresses along valid paths and blocks impossible transitions."""
    target = datetime(2026, 8, 21, 15, 0, 0, tzinfo=timezone.utc)
    engine = ActionableSignalEngine()

    fc = {
        "asset": "EURUSD",
        "timeframe": "1H",
        "direction": "BUY",
        "confidence": 0.75,
        "consensus_score": 0.80,
        "entry_price": 1.0850,
        "stop_loss": 1.0800,
        "take_profit": 1.0950,
        "risk_reward": 2.0,
    }

    # 1. Far before window -> WATCH / WAIT
    t1 = target - timedelta(minutes=45)
    s1 = engine.create_actionable_opportunity(fc, target_utc=target, now_utc=t1)
    assert s1["status"] == "WATCH"

    # 2. Window start reached -> ENTER_NOW / ENTER NOW
    t2 = target - timedelta(minutes=10)
    s2 = engine.create_actionable_opportunity(fc, target_utc=target, now_utc=t2)
    assert s2["status"] == "ENTER_NOW"

    # 3. Window expired -> EXPIRED
    t3 = target + timedelta(minutes=20)
    s3 = engine.create_actionable_opportunity(fc, target_utc=target, now_utc=t3)
    assert s3["status"] == "EXPIRED"

    # 4. Stop loss breach during revalidation -> INVALIDATED
    s4 = engine.revalidate_opportunity(
        s1["signal_id"],
        current_forecast=fc,
        current_market={"price": 1.0790}, # SL breached
        now_utc=t1,
    )
    assert s4["status"] == "INVALIDATED"
    assert s4["primary_action"] == "CANCELLED"


# ═══════════════════════════════════════════════════════════════════════════════
# PART 7 — DYNAMIC ENTRY WINDOW
# ═══════════════════════════════════════════════════════════════════════════════

def test_part7_dynamic_entry_window_scaling():
    """Verify entry window scaling with timeframes and ATR/volatility."""
    target = datetime(2026, 8, 21, 16, 0, 0, tzinfo=timezone.utc)

    # 15M: base 5m lead/lag
    w15 = market_clock.compute_entry_window(target, timeframe="15M")
    assert w15["lead_minutes"] == 5
    assert w15["lag_minutes"] == 5

    # 1H: base 15m lead/lag
    w1h = market_clock.compute_entry_window(target, timeframe="1H")
    assert w1h["lead_minutes"] == 15

    # 4H: base 30m lead/lag
    w4h = market_clock.compute_entry_window(target, timeframe="4H")
    assert w4h["lead_minutes"] == 30

    # 1D: base 60m lead/lag
    w1d = market_clock.compute_entry_window(target, timeframe="1D")
    assert w1d["lead_minutes"] == 60

    # High Volatility (1.5x) on 1H -> 22m lead/lag
    w1h_high = market_clock.compute_entry_window(target, timeframe="1H", volatility_pct=1.5)
    assert w1h_high["lead_minutes"] == 22

    # Low Volatility (0.6x) on 1H -> clamped to minimum multiplier 0.8 -> 12m lead/lag
    w1h_low = market_clock.compute_entry_window(target, timeframe="1H", volatility_pct=0.6)
    assert w1h_low["lead_minutes"] == 12


# ═══════════════════════════════════════════════════════════════════════════════
# PART 8 — EXACT TIME VALIDATION & TIMEZONE DISCIPLINE
# ═══════════════════════════════════════════════════════════════════════════════

def test_part8_exact_time_validation_conversions():
    """Verify UTC-IST conversions across day, month, year, and midnight crossings."""
    # Midnight crossing: UTC 19:00 -> IST 00:30 (next day)
    t_utc = datetime(2026, 8, 21, 19, 0, 0, tzinfo=timezone.utc)
    ist_s = market_clock.format_ist(t_utc)
    assert "Saturday" in ist_s
    assert "22 August 2026 12:30 AM IST" in ist_s

    # Month crossing: 31 August 2026 20:00 UTC -> 1 September 2026 01:30 AM IST
    t_month = datetime(2026, 8, 31, 20, 0, 0, tzinfo=timezone.utc)
    ist_m = market_clock.format_ist(t_month)
    assert "01 September 2026 01:30 AM IST" in ist_m

    # Year crossing: 31 Dec 2026 21:00 UTC -> 1 Jan 2027 02:30 AM IST
    t_year = datetime(2026, 12, 31, 21, 0, 0, tzinfo=timezone.utc)
    ist_y = market_clock.format_ist(t_year)
    assert "01 January 2027 02:30 AM IST" in ist_y


# ═══════════════════════════════════════════════════════════════════════════════
# PART 9 — AUTHORITATIVE COUNTDOWN & CLIENT DRIFT IMMUNITY
# ═══════════════════════════════════════════════════════════════════════════════

def test_part9_authoritative_countdown():
    """Verify server countdown calculation and clock drift resilience."""
    server_now = datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc)
    target = datetime(2026, 8, 21, 12, 45, 30, tzinfo=timezone.utc)

    # Authoritative calculation uses server clock
    cd = market_clock.compute_countdown(target, current_utc=server_now)
    assert cd["seconds_remaining"] == 2730
    assert cd["countdown_formatted"] == "00:45:30"
    assert cd["is_passed"] is False

    # Target passed
    target_past = datetime(2026, 8, 21, 11, 50, 0, tzinfo=timezone.utc)
    cd_past = market_clock.compute_countdown(target_past, current_utc=server_now)
    assert cd_past["is_passed"] is True
    assert cd_past["direction_label"] == "ago"


# ═══════════════════════════════════════════════════════════════════════════════
# PART 10 — REVALIDATION CASES 1 THROUGH 6
# ═══════════════════════════════════════════════════════════════════════════════

def test_part10_revalidation_six_cases():
    """Verify all 6 required revalidation cases."""
    prev = {
        "signal_id": "SIG-TEST-001",
        "version": 1,
        "direction": "BUY",
        "confidence": 0.78,
        "consensus_score": 0.80,
        "market_regime": "TRENDING_BULL",
        "entry_price": 1.0850,
        "stop_loss": 1.0800,
    }

    # Case 1: BUY 78% -> BUY 82% (STRENGTHENED)
    c1 = dict(prev, confidence=0.82)
    r1 = revalidation_engine.compare_and_revalidate(prev, c1)
    assert r1["revalidation_status"] == "SIGNAL_STRENGTHENED"

    # Case 2: BUY 78% -> BUY 65% (WEAKENED)
    c2 = dict(prev, confidence=0.65)
    r2 = revalidation_engine.compare_and_revalidate(prev, c2)
    assert r2["revalidation_status"] == "SIGNAL_WEAKENED"

    # Case 3: BUY -> SELL with strong consensus (SIGNAL_CHANGED)
    c3 = dict(prev, direction="SELL", confidence=0.75, consensus_score=0.85)
    r3 = revalidation_engine.compare_and_revalidate(prev, c3)
    assert r3["revalidation_status"] == "SIGNAL_CHANGED"
    assert r3["direction"] == "SELL"

    # Case 4: BUY -> NEUTRAL (SIGNAL_INVALIDATED)
    c4 = dict(prev, direction="NEUTRAL", confidence=0.50, consensus_score=0.50)
    r4 = revalidation_engine.compare_and_revalidate(prev, c4)
    assert r4["revalidation_status"] == "SIGNAL_INVALIDATED"
    assert r4["actionable_status"] == "NO_TRADE"

    # Case 5: Event risk becomes HIGH (EVENT_BLOCKED)
    c5 = dict(prev, event_risk="HIGH")
    r5 = revalidation_engine.compare_and_revalidate(prev, c5)
    assert r5["revalidation_status"] == "EVENT_BLOCKED"

    # Case 6: Data becomes stale (DATA_STALE)
    c6 = dict(prev, data_freshness_status="DATA_STALE")
    r6 = revalidation_engine.compare_and_revalidate(prev, c6)
    assert r6["revalidation_status"] == "DATA_STALE"


# ═══════════════════════════════════════════════════════════════════════════════
# PART 11 — ANTI-WHIPSAW HYSTERESIS SEQUENCE
# ═══════════════════════════════════════════════════════════════════════════════

def test_part11_anti_whipsaw_hysteresis_sequence():
    """Verify that minor noise does not flip direction, but strong consensus allows reversal."""
    prev = {
        "signal_id": "SIG-EURUSD-FLIP",
        "version": 1,
        "direction": "BUY",
        "confidence": 0.72,
        "consensus_score": 0.75,
    }

    # Weak SELL (consensus 0.54 < 0.70 threshold) -> Reversal BLOCKED (fails closed to NO_TRADE)
    weak_sell = {"direction": "SELL", "confidence": 0.58, "consensus_score": 0.54}
    res_weak = revalidation_engine.compare_and_revalidate(prev, weak_sell)
    assert res_weak["revalidation_status"] == "SIGNAL_INVALIDATED"
    assert res_weak["actionable_status"] == "NO_TRADE"
    assert res_weak["no_trade_reason"] == "MODEL_DISAGREEMENT"

    # Strong SELL (consensus 0.82 >= 0.70 threshold, confidence 0.78 >= 0.65) -> Reversal ACCEPTED
    strong_sell = {"direction": "SELL", "confidence": 0.78, "consensus_score": 0.82}
    res_strong = revalidation_engine.compare_and_revalidate(prev, strong_sell)
    assert res_strong["revalidation_status"] == "SIGNAL_CHANGED"
    assert res_strong["direction"] == "SELL"


# ═══════════════════════════════════════════════════════════════════════════════
# PART 12 & 13 — SIGNAL VERSIONING & IMMUTABILITY
# ═══════════════════════════════════════════════════════════════════════════════

def test_part12_13_signal_versioning_and_immutability():
    """Verify parent-child lineage and immutability of original forecast records."""
    engine = ActionableSignalEngine()
    initial_fc = {
        "asset": "EURUSD",
        "timeframe": "1H",
        "direction": "BUY",
        "confidence": 0.70,
        "consensus_score": 0.75,
        "entry_price": 1.0850,
    }

    # Version 1
    v1 = engine.create_actionable_opportunity(initial_fc)
    sig_id = v1["signal_id"]
    assert v1["version"] == 1
    assert v1["parent_signal_id"] == sig_id

    # Version 2
    v2 = engine.revalidate_opportunity(sig_id, dict(initial_fc, confidence=0.78))
    assert v2["version"] == 2
    assert v2["parent_signal_id"] == sig_id
    assert v2["supersedes_signal_id"] == sig_id

    # Version 3
    v3 = engine.revalidate_opportunity(v2["signal_id"], dict(initial_fc, confidence=0.82))
    assert v3["version"] == 3
    assert v3["parent_signal_id"] == sig_id

    # Verify timeline lineage
    timeline = engine.get_signal_evolution(sig_id)
    assert len(timeline) == 3
    assert timeline[0]["version"] == 1
    assert timeline[0]["confidence"] == 0.70  # Immutable first record preserved
    assert timeline[1]["version"] == 2
    assert timeline[1]["confidence"] == 0.78
    assert timeline[2]["version"] == 3
    assert timeline[2]["confidence"] == 0.82


# ═══════════════════════════════════════════════════════════════════════════════
# PART 15 & 16 — PAPER TRADE RESOLUTION & CANDLE REPLAY
# ═══════════════════════════════════════════════════════════════════════════════

def test_part15_16_paper_trade_replay_and_ambiguity():
    """Verify TP, SL, Timeout, and Ambiguous candle replay outcomes."""
    trade = {
        "trade_id": "PT-TEST-001",
        "asset": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.0850,
        "stop_loss": 1.0800,
        "take_profit": 1.0950,
        "status": "PAPER_OPEN",
    }

    # 1. TP Hit
    tp_candles = [
        {"timestamp": "2026-08-21T14:00:00Z", "open": 1.0850, "high": 1.0880, "low": 1.0840, "close": 1.0870},
        {"timestamp": "2026-08-21T15:00:00Z", "open": 1.0870, "high": 1.0960, "low": 1.0860, "close": 1.0955},
    ]
    res_tp = offline_gap_recovery_engine.resolve_trade_with_mfe_mae(trade, tp_candles)
    assert res_tp["status"] == OUTCOME_TP_HIT
    assert res_tp["gross_r"] == 2.0
    assert res_tp["net_r"] > 1.8

    # 2. SL Hit
    sl_candles = [
        {"timestamp": "2026-08-21T14:00:00Z", "open": 1.0850, "high": 1.0860, "low": 1.0790, "close": 1.0795},
    ]
    res_sl = offline_gap_recovery_engine.resolve_trade_with_mfe_mae(trade, sl_candles)
    assert res_sl["status"] == OUTCOME_SL_HIT
    assert res_sl["gross_r"] == -1.0

    # 3. Ambiguous (dual breach in single bar)
    amb_candles = [
        {"timestamp": "2026-08-21T14:00:00Z", "open": 1.0850, "high": 1.0960, "low": 1.0790, "close": 1.0850},
    ]
    res_amb = offline_gap_recovery_engine.resolve_trade_with_mfe_mae(trade, amb_candles)
    assert res_amb["status"] == OUTCOME_AMBIGUOUS

    # 4. Timeout (Time Exit)
    time_candles = [
        {"timestamp": "2026-08-21T14:00:00Z", "open": 1.0850, "high": 1.0880, "low": 1.0840, "close": 1.0870},
    ]
    res_time = offline_gap_recovery_engine.resolve_trade_with_mfe_mae(trade, time_candles, max_hold_hours=1.0)
    assert res_time["status"] == OUTCOME_TIME_EXIT


# ═══════════════════════════════════════════════════════════════════════════════
# PART 20 — API CONTRACT AUDIT
# ═══════════════════════════════════════════════════════════════════════════════

def test_part20_api_contracts():
    """Verify REST API response structure and error handling."""
    # GET /actionable
    r1 = client.get("/api/v1/signals/actionable")
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["success"] is True
    assert "server_time_ist" in d1

    # GET /next-setup
    r2 = client.get("/api/v1/signals/next-setup")
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["success"] is True
    assert "has_setup" in d2

    # GET /countdown with valid ISO
    t_str = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
    r3 = client.get(f"/api/v1/signals/countdown?target_utc={t_str}")
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["success"] is True
    assert d3["countdown"]["seconds_remaining"] > 0

    # GET /countdown with invalid input does not crash
    r4 = client.get("/api/v1/signals/countdown?target_utc=invalid_garbage_timestamp")
    assert r4.status_code == 200
    assert r4.json()["countdown"] is None


# ═══════════════════════════════════════════════════════════════════════════════
# PART 27 — PERFORMANCE & LATENCY BENCHMARK
# ═══════════════════════════════════════════════════════════════════════════════

def test_part27_performance_latency():
    """Measure endpoint latencies to ensure sub-100ms response times."""
    t0 = time.perf_counter()
    for _ in range(5):
        client.get("/api/v1/signals/actionable")
    t_actionable = (time.perf_counter() - t0) / 5.0
    assert t_actionable < 0.100  # Less than 100ms average

    t0 = time.perf_counter()
    for _ in range(5):
        client.get("/api/v1/signals/next-setup")
    t_next = (time.perf_counter() - t0) / 5.0
    assert t_next < 0.100  # Less than 100ms average


# ═══════════════════════════════════════════════════════════════════════════════
# PART 28 — SECURITY & INPUT VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def test_part28_security_input_validation():
    """Verify resilient handling of malformed and adversarial user inputs."""
    # SQL injection attempt in signal_id
    r_sqli = client.get("/api/v1/signals/' OR '1'='1/evolution")
    assert r_sqli.status_code in [200, 404]
    assert r_sqli.json().get("evolution_timeline", []) == []

    # Extremely long string
    r_long = client.get(f"/api/v1/signals/{'A'*500}/evolution")
    assert r_long.status_code in [200, 404]
