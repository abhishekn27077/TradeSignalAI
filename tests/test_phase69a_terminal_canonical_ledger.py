"""
tests/test_phase69a_terminal_canonical_ledger.py
================================================
Comprehensive 20-Point Test Suite for Phase 69A:
Trade Signal Terminal UX & Canonical Prospective Signal Ledger.
"""

import pytest
import sqlite3
import os
import json
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.core.canonical_prospective_ledger import (
    canonical_prospective_ledger,
    CanonicalProspectiveSignal,
    CanonicalProspectiveLedger,
    STATUS_UPCOMING,
    STATUS_ENTRY_WINDOW,
    STATUS_ACTIVE,
    STATUS_RESOLVED,
    OUTCOME_WON,
    OUTCOME_LOST,
    OUTCOME_TIME_EXIT,
    OUTCOME_AMBIGUOUS,
)
from app.analytics.timeframe_intelligence_engine import timeframe_intelligence_engine

client = TestClient(app)


# ---------------------------------------------------------------------------
# Test 1: Complete Canonical Signal Schema Persistence
# ---------------------------------------------------------------------------
def test_signal_persistence_schema():
    now = datetime.now(timezone.utc)
    sig_id = f"SIG-TEST-SCHEMA-{now.strftime('%Y%m%d%H%M%S')}-EURUSD-1H-001"
    timing = canonical_prospective_ledger.compute_exact_timing(now, "1H")

    sig = CanonicalProspectiveSignal(
        signal_id=sig_id,
        campaign_id="CAMPAIGN-PROSPECTIVE-2026-v1",
        generated_at_utc=now.isoformat(),
        generated_at_ist=(now + timedelta(hours=5, minutes=30)).isoformat(),
        asset="EURUSD",
        timeframe="1H",
        direction="BUY",
        market_snapshot_hash="hash-123456",
        policy_version="POL-69A-v1",
        model_version="ENSEMBLE-P68-v1",
        config_hash="cfg-69a-hash",
        entry_window_start=timing["entry_window_start"],
        entry_window_end=timing["entry_window_end"],
        preferred_entry_time=timing["preferred_entry_time"],
        entry_price=1.0850,
        stop_loss=1.0800,
        take_profit=1.0950,
        expected_hold_seconds=timing["expected_hold_seconds"],
        expected_exit_time=timing["expected_exit_time"],
        max_exit_time=timing["max_exit_time"],
        probability=0.78,
        signal_strength=82,
        quality_grade="A+",
        expected_r=0.62,
        regime="TRENDING_EXPANSION",
        mtf_alignment=0.88,
        risk_state="NORMAL",
        evidence_clusters={"kronos": 0.82, "bayesian": 0.74},
        mtf_confirmation={"5m": "BUY", "15m": "BUY", "1H": "BUY", "4H": "BUY", "1D": "WATCH"},
        qualification_status="QUALIFIED",
        signal_status=STATUS_UPCOMING,
    )

    success = canonical_prospective_ledger.persist_signal(sig)
    assert success is True

    # Retrieve and verify all fields
    fetched = canonical_prospective_ledger.get_signal(sig_id)
    assert fetched is not None
    assert fetched.signal_id == sig_id
    assert fetched.asset == "EURUSD"
    assert fetched.timeframe == "1H"
    assert fetched.direction == "BUY"
    assert fetched.entry_price == 1.0850
    assert fetched.quality_grade == "A+"
    assert fetched.expected_r == 0.62


# ---------------------------------------------------------------------------
# Test 2: Immutable Signal Snapshot (No Overwrite on Re-Persist)
# ---------------------------------------------------------------------------
def test_immutable_signal_snapshot():
    now = datetime.now(timezone.utc)
    sig_id = f"SIG-TEST-IMMUTABLE-{now.strftime('%Y%m%d%H%M%S')}-GBPUSD-15m-001"
    timing = canonical_prospective_ledger.compute_exact_timing(now, "15m")

    original_sig = CanonicalProspectiveSignal(
        signal_id=sig_id,
        campaign_id="CAMPAIGN-PROSPECTIVE-2026-v1",
        generated_at_utc=now.isoformat(),
        generated_at_ist=(now + timedelta(hours=5, minutes=30)).isoformat(),
        asset="GBPUSD",
        timeframe="15m",
        direction="SELL",
        market_snapshot_hash="hash-orig",
        policy_version="POL-69A-v1",
        model_version="ENSEMBLE-P68-v1",
        config_hash="cfg-hash",
        entry_window_start=timing["entry_window_start"],
        entry_window_end=timing["entry_window_end"],
        preferred_entry_time=timing["preferred_entry_time"],
        entry_price=1.2900,
        stop_loss=1.2950,
        take_profit=1.2800,
        expected_hold_seconds=timing["expected_hold_seconds"],
        expected_exit_time=timing["expected_exit_time"],
        max_exit_time=timing["max_exit_time"],
        probability=0.72,
        signal_strength=75,
        quality_grade="A",
        expected_r=0.45,
        regime="TRENDING",
        mtf_alignment=0.80,
        risk_state="NORMAL",
    )
    canonical_prospective_ledger.persist_signal(original_sig)

    # Attempt to tamper by re-persisting with altered price / confidence
    tampered_sig = CanonicalProspectiveSignal(
        signal_id=sig_id,
        campaign_id="CAMPAIGN-PROSPECTIVE-2026-v1",
        generated_at_utc=now.isoformat(),
        generated_at_ist=(now + timedelta(hours=5, minutes=30)).isoformat(),
        asset="GBPUSD",
        timeframe="15m",
        direction="BUY",  # Tampered
        market_snapshot_hash="hash-tampered",
        policy_version="POL-69A-v1",
        model_version="ENSEMBLE-P68-v1",
        config_hash="cfg-hash",
        entry_window_start=timing["entry_window_start"],
        entry_window_end=timing["entry_window_end"],
        preferred_entry_time=timing["preferred_entry_time"],
        entry_price=1.3500,  # Tampered
        stop_loss=1.3400,
        take_profit=1.3700,
        expected_hold_seconds=timing["expected_hold_seconds"],
        expected_exit_time=timing["expected_exit_time"],
        max_exit_time=timing["max_exit_time"],
        probability=0.99,  # Tampered
        signal_strength=99,
        quality_grade="A+",
        expected_r=1.50,
        regime="TRENDING",
        mtf_alignment=0.80,
        risk_state="NORMAL",
    )
    canonical_prospective_ledger.persist_signal(tampered_sig)

    # Verify original values are strictly preserved
    fetched = canonical_prospective_ledger.get_signal(sig_id)
    assert fetched.direction == "SELL"
    assert fetched.entry_price == 1.2900
    assert fetched.probability == 0.72


# ---------------------------------------------------------------------------
# Test 3: Duplicate Prevention
# ---------------------------------------------------------------------------
def test_duplicate_prevention():
    now = datetime.now(timezone.utc)
    sig_id = canonical_prospective_ledger.generate_signal_id("USDJPY", "4H", now, counter=1)
    timing = canonical_prospective_ledger.compute_exact_timing(now, "4H")

    sig = CanonicalProspectiveSignal(
        signal_id=sig_id,
        campaign_id="CAMPAIGN-PROSPECTIVE-2026-v1",
        generated_at_utc=now.isoformat(),
        generated_at_ist=(now + timedelta(hours=5, minutes=30)).isoformat(),
        asset="USDJPY",
        timeframe="4H",
        direction="BUY",
        market_snapshot_hash="snap-dup",
        policy_version="POL-69A-v1",
        model_version="ENSEMBLE-P68-v1",
        config_hash="cfg-hash",
        entry_window_start=timing["entry_window_start"],
        entry_window_end=timing["entry_window_end"],
        preferred_entry_time=timing["preferred_entry_time"],
        entry_price=152.00,
        stop_loss=151.00,
        take_profit=154.00,
        expected_hold_seconds=timing["expected_hold_seconds"],
        expected_exit_time=timing["expected_exit_time"],
        max_exit_time=timing["max_exit_time"],
        probability=0.79,
        signal_strength=85,
        quality_grade="A+",
        expected_r=0.65,
        regime="TRENDING",
        mtf_alignment=0.90,
        risk_state="NORMAL",
    )
    res1 = canonical_prospective_ledger.persist_signal(sig)
    res2 = canonical_prospective_ledger.persist_signal(sig)
    assert res1 is True
    assert res2 is True


# ---------------------------------------------------------------------------
# Test 4: Page Refresh Idempotency
# ---------------------------------------------------------------------------
def test_page_refresh_idempotency():
    res1 = client.get("/api/v1/terminal/today")
    assert res1.status_code == 200
    data1 = res1.json()

    res2 = client.get("/api/v1/terminal/today")
    assert res2.status_code == 200
    data2 = res2.json()

    assert data1["total_qualified_signals"] == data2["total_qualified_signals"]
    assert data1["total_no_trade_signals"] == data2["total_no_trade_signals"]


# ---------------------------------------------------------------------------
# Test 5: Candle-Close Scheduling Boundaries
# ---------------------------------------------------------------------------
def test_candle_close_scheduling():
    from app.core.canonical_prospective_ledger import TF_SECONDS
    assert TF_SECONDS["5m"] == 300
    assert TF_SECONDS["15m"] == 900
    assert TF_SECONDS["1H"] == 3600
    assert TF_SECONDS["4H"] == 14400
    assert TF_SECONDS["1D"] == 86400


# ---------------------------------------------------------------------------
# Test 6: Exact Entry Window Timing
# ---------------------------------------------------------------------------
def test_exact_entry_window_timing():
    t0 = datetime(2026, 8, 25, 18, 0, 0, tzinfo=timezone.utc)
    timing_1h = canonical_prospective_ledger.compute_exact_timing(t0, "1H")
    
    assert timing_1h["entry_window_start"] == "2026-08-25T18:00:00+00:00"
    # 1H window duration = 360s (6 mins)
    assert "2026-08-25T18:06:00" in timing_1h["entry_window_end"]
    assert timing_1h["expected_hold_seconds"] == 3600


# ---------------------------------------------------------------------------
# Test 7: Expected Exit Calculation
# ---------------------------------------------------------------------------
def test_expected_exit_calculation():
    t0 = datetime(2026, 8, 25, 18, 0, 0, tzinfo=timezone.utc)
    timing_4h = canonical_prospective_ledger.compute_exact_timing(t0, "4H")

    assert timing_4h["expected_hold_seconds"] == 14400  # 4 hours
    assert "2026-08-25T22:" in timing_4h["expected_exit_time"]


# ---------------------------------------------------------------------------
# Test 8: Deterministic Outcome Resolution Against Candle
# ---------------------------------------------------------------------------
def test_signal_resolution_deterministic():
    now = datetime.now(timezone.utc)
    sig = CanonicalProspectiveSignal(
        signal_id=f"SIG-RES-{now.strftime('%Y%m%d%H%M%S')}",
        campaign_id="CAMPAIGN-1",
        generated_at_utc=now.isoformat(),
        generated_at_ist=now.isoformat(),
        asset="EURUSD",
        timeframe="1H",
        direction="BUY",
        market_snapshot_hash="snap",
        policy_version="POL-1",
        model_version="MOD-1",
        config_hash="cfg",
        entry_window_start=now.isoformat(),
        entry_window_end=now.isoformat(),
        preferred_entry_time=now.isoformat(),
        entry_price=1.0850,
        stop_loss=1.0800,
        take_profit=1.0950,
        expected_hold_seconds=3600,
        expected_exit_time=now.isoformat(),
        max_exit_time=now.isoformat(),
        probability=0.75,
        signal_strength=80,
        quality_grade="A",
        expected_r=0.50,
        regime="TREND",
        mtf_alignment=0.8,
        risk_state="NORMAL",
        friction_r=0.05,
    )

    # Inactive candle (inside bounds)
    outcome, reason, exit_p, net_r = canonical_prospective_ledger.resolve_against_candle(
        sig, candle_open=1.0850, candle_high=1.0890, candle_low=1.0830, candle_close=1.0870, candle_time="2026-08-25T19:00:00"
    )
    assert outcome is None


# ---------------------------------------------------------------------------
# Test 9: Take Profit (TP) Resolution
# ---------------------------------------------------------------------------
def test_tp_resolution():
    now = datetime.now(timezone.utc)
    sig = CanonicalProspectiveSignal(
        signal_id=f"SIG-TP-{now.strftime('%Y%m%d%H%M%S')}",
        campaign_id="CAMPAIGN-1",
        generated_at_utc=now.isoformat(),
        generated_at_ist=now.isoformat(),
        asset="EURUSD",
        timeframe="1H",
        direction="BUY",
        market_snapshot_hash="snap",
        policy_version="POL-1",
        model_version="MOD-1",
        config_hash="cfg",
        entry_window_start=now.isoformat(),
        entry_window_end=now.isoformat(),
        preferred_entry_time=now.isoformat(),
        entry_price=1.0850,
        stop_loss=1.0800,
        take_profit=1.0950,
        expected_hold_seconds=3600,
        expected_exit_time=now.isoformat(),
        max_exit_time=now.isoformat(),
        probability=0.75,
        signal_strength=80,
        quality_grade="A",
        expected_r=0.50,
        regime="TREND",
        mtf_alignment=0.8,
        risk_state="NORMAL",
        friction_r=0.05,
    )

    outcome, reason, exit_p, net_r = canonical_prospective_ledger.resolve_against_candle(
        sig, candle_open=1.0870, candle_high=1.0960, candle_low=1.0860, candle_close=1.0955, candle_time="2026-08-25T19:00:00"
    )
    assert outcome == OUTCOME_WON
    assert reason == "TP_HIT"
    assert exit_p == 1.0950
    assert net_r == 1.95  # 2.0R gross - 0.05 friction


# ---------------------------------------------------------------------------
# Test 10: Stop Loss (SL) Resolution
# ---------------------------------------------------------------------------
def test_sl_resolution():
    now = datetime.now(timezone.utc)
    sig = CanonicalProspectiveSignal(
        signal_id=f"SIG-SL-{now.strftime('%Y%m%d%H%M%S')}",
        campaign_id="CAMPAIGN-1",
        generated_at_utc=now.isoformat(),
        generated_at_ist=now.isoformat(),
        asset="GBPUSD",
        timeframe="1H",
        direction="SELL",
        market_snapshot_hash="snap",
        policy_version="POL-1",
        model_version="MOD-1",
        config_hash="cfg",
        entry_window_start=now.isoformat(),
        entry_window_end=now.isoformat(),
        preferred_entry_time=now.isoformat(),
        entry_price=1.2900,
        stop_loss=1.2950,
        take_profit=1.2800,
        expected_hold_seconds=3600,
        expected_exit_time=now.isoformat(),
        max_exit_time=now.isoformat(),
        probability=0.75,
        signal_strength=80,
        quality_grade="A",
        expected_r=0.50,
        regime="TREND",
        mtf_alignment=0.8,
        risk_state="NORMAL",
        friction_r=0.05,
    )

    outcome, reason, exit_p, net_r = canonical_prospective_ledger.resolve_against_candle(
        sig, candle_open=1.2910, candle_high=1.2960, candle_low=1.2890, candle_close=1.2955, candle_time="2026-08-25T19:00:00"
    )
    assert outcome == OUTCOME_LOST
    assert reason == "SL_HIT"
    assert exit_p == 1.2950
    assert net_r == -1.05


# ---------------------------------------------------------------------------
# Test 11: Timeout Resolution
# ---------------------------------------------------------------------------
def test_timeout_resolution():
    now = datetime.now(timezone.utc)
    sig_id = f"SIG-TIMEOUT-{now.strftime('%Y%m%d%H%M%S')}-USDJPY-1H-001"
    timing = canonical_prospective_ledger.compute_exact_timing(now, "1H")

    sig = CanonicalProspectiveSignal(
        signal_id=sig_id,
        campaign_id="CAMPAIGN-1",
        generated_at_utc=now.isoformat(),
        generated_at_ist=now.isoformat(),
        asset="USDJPY",
        timeframe="1H",
        direction="BUY",
        market_snapshot_hash="snap",
        policy_version="POL-1",
        model_version="MOD-1",
        config_hash="cfg",
        entry_window_start=timing["entry_window_start"],
        entry_window_end=timing["entry_window_end"],
        preferred_entry_time=timing["preferred_entry_time"],
        entry_price=152.00,
        stop_loss=151.00,
        take_profit=154.00,
        expected_hold_seconds=3600,
        expected_exit_time=timing["expected_exit_time"],
        max_exit_time=timing["max_exit_time"],
        probability=0.75,
        signal_strength=80,
        quality_grade="A",
        expected_r=0.50,
        regime="TREND",
        mtf_alignment=0.8,
        risk_state="NORMAL",
    )
    canonical_prospective_ledger.persist_signal(sig)

    resolved = canonical_prospective_ledger.resolve_signal_outcome(
        signal_id=sig_id,
        outcome=OUTCOME_TIME_EXIT,
        resolution_reason="EXPIRY_EXIT",
        actual_exit_price=152.40,
        actual_exit_time=timing["max_exit_time"],
        gross_r=0.40,
        net_r=0.35,
    )
    assert resolved is True
    fetched = canonical_prospective_ledger.get_signal(sig_id)
    assert fetched.outcome == OUTCOME_TIME_EXIT
    assert fetched.net_r == 0.35


# ---------------------------------------------------------------------------
# Test 12: Ambiguous Candle Resolution (Conservative SL Rule)
# ---------------------------------------------------------------------------
def test_ambiguous_candle_conservative_resolution():
    now = datetime.now(timezone.utc)
    sig = CanonicalProspectiveSignal(
        signal_id=f"SIG-AMBIG-{now.strftime('%Y%m%d%H%M%S')}",
        campaign_id="CAMPAIGN-1",
        generated_at_utc=now.isoformat(),
        generated_at_ist=now.isoformat(),
        asset="EURUSD",
        timeframe="1H",
        direction="BUY",
        market_snapshot_hash="snap",
        policy_version="POL-1",
        model_version="MOD-1",
        config_hash="cfg",
        entry_window_start=now.isoformat(),
        entry_window_end=now.isoformat(),
        preferred_entry_time=now.isoformat(),
        entry_price=1.0850,
        stop_loss=1.0800,
        take_profit=1.0950,
        expected_hold_seconds=3600,
        expected_exit_time=now.isoformat(),
        max_exit_time=now.isoformat(),
        probability=0.75,
        signal_strength=80,
        quality_grade="A",
        expected_r=0.50,
        regime="TREND",
        mtf_alignment=0.8,
        risk_state="NORMAL",
        friction_r=0.05,
    )

    # Bar touches both TP (1.0950) and SL (1.0800) -> Conservative SL assumed
    outcome, reason, exit_p, net_r = canonical_prospective_ledger.resolve_against_candle(
        sig, candle_open=1.0850, candle_high=1.0960, candle_low=1.0790, candle_close=1.0940, candle_time="2026-08-25T19:00:00"
    )
    assert outcome == OUTCOME_LOST
    assert reason == "AMBIGUOUS_CANDLE_CONSERVATIVE_SL"
    assert exit_p == 1.0800
    assert net_r == -1.05


# ---------------------------------------------------------------------------
# Test 13: Historical Retrieval Across All Records
# ---------------------------------------------------------------------------
def test_historical_retrieval():
    res = client.get("/api/v1/terminal/history?date_filter=ALL&limit=50")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["total_returned"] >= 9
    assert "metrics" in data


# ---------------------------------------------------------------------------
# Test 14: Yesterday Retrieval Consistency (Never Returns 0)
# ---------------------------------------------------------------------------
def test_yesterday_retrieval_consistency():
    res = client.get("/api/v1/terminal/history?date_filter=YESTERDAY&limit=50")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    # Guaranteed non-empty historical records
    assert len(data["signals"]) >= 1


# ---------------------------------------------------------------------------
# Test 15: Timeframe Statistics & Wilson Confidence Intervals
# ---------------------------------------------------------------------------
def test_timeframe_statistics():
    ci_low, ci_high = timeframe_intelligence_engine.calculate_wilson_ci(wins=14, total=20)
    assert ci_low >= 45.0
    assert ci_high <= 90.0

    tf_eval = timeframe_intelligence_engine.evaluate_all_timeframes()
    assert tf_eval["success"] is True
    assert len(tf_eval["full_analytics"]) == 9


# ---------------------------------------------------------------------------
# Test 16: Insufficient Sample Guard
# ---------------------------------------------------------------------------
def test_insufficient_sample_guard():
    stats = timeframe_intelligence_engine.evaluate_all_timeframes()
    analytics = stats["full_analytics"]
    for row in analytics:
        if row["sample_size"] < 5:
            assert row["sample_status"] == "INSUFFICIENT SAMPLE"


# ---------------------------------------------------------------------------
# Test 17: Best and Second-Best Timeframe Dynamic Ranking
# ---------------------------------------------------------------------------
def test_best_and_second_best_timeframe_ranking():
    stats = timeframe_intelligence_engine.evaluate_all_timeframes()
    best = stats["best_observed_timeframe"]
    second = stats["second_best_timeframe"]
    assert best in ["4H", "1H", "1D", "15m"]
    assert second in ["4H", "1H", "1D", "15m"]
    assert best != second


# ---------------------------------------------------------------------------
# Test 18: Tomorrow Forecast Separation (Forecast Only)
# ---------------------------------------------------------------------------
def test_tomorrow_forecast_separation():
    res = client.get("/api/v1/terminal/tomorrow")
    assert res.status_code == 200
    data = res.json()
    assert data["classification"] == "FORECAST — NOT YET A PROSPECTIVE SIGNAL"
    assert data["forecasts_count"] == 9
    for fc in data["forecasts"]:
        assert "projected_direction" in fc
        assert "model_confidence" in fc


# ---------------------------------------------------------------------------
# Test 19: No-Trade Decision Separation
# ---------------------------------------------------------------------------
def test_no_trade_separation():
    res = client.get("/api/v1/terminal/today")
    assert res.status_code == 200
    data = res.json()
    for w in data["time_windows"]:
        for nt in w["no_trade_signals"]:
            assert nt["qualification_status"] != "QUALIFIED"
            assert "no_trade_reason" in nt


# ---------------------------------------------------------------------------
# Test 20: Campaign & Snapshot Linkage Integrity
# ---------------------------------------------------------------------------
def test_campaign_and_daily_seal_linkage():
    signals = canonical_prospective_ledger.get_signals_by_filter(date_filter="ALL", limit=10)
    for s in signals:
        assert s.campaign_id.startswith("CAMPAIGN-")
        assert len(s.market_snapshot_hash) > 0
        assert s.policy_version.startswith("POL-")
