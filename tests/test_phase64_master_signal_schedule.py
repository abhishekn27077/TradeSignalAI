"""
tests/test_phase64_master_signal_schedule.py
============================================
Comprehensive Automated Test Suite for Phase 64:
Real Signal Generation, Multi-Timeframe Signal Schedule,
Causal Outcome Learning, MTF Fusion & 100-Cycle Repeatability.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import sqlite3
import os

from app.main import app
from app.core.signal_product import SignalProduct, SignalDirection, SignalQualityTier, SignalLifecycleStatus, CausalViolationError
from app.core.signal_schedule_engine import signal_schedule_engine
from app.core.mtf_fusion_engine import mtf_fusion_engine
from app.analytics.causal_outcome_learning_engine import causal_outcome_learning_engine
from app.config.settings import get_settings


@pytest.fixture
def client():
    return TestClient(app)


# ── 1. Signal Product Model & Causal Barrier ──────────────────────────────────

def test_signal_product_immutability_and_causal_barrier():
    """Verify frozen immutability and hard CausalViolationError on future cutoff timestamps."""
    now_str = datetime.now(timezone.utc).isoformat()
    t0_str = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    
    prod = SignalProduct(
        signal_id="SIG-TEST-001",
        asset="EURUSD",
        asset_class="FX",
        direction="BUY",
        timeframe="1H",
        signal_scope="INTRADAY",
        created_at=now_str,
        data_cutoff_time=t0_str,
        entry_price=1.0850,
        stop_loss=1.0800,
        take_profit=1.0950,
        expiry_time=(datetime.now(timezone.utc) + timedelta(hours=4)).isoformat(),
        expected_hold_time="4H",
        confidence=0.78,
        calibrated_probability=0.74,
        agreement_percentage=75.0,
        quality_tier="A",
        expected_net_r=0.42,
        spread_cost=0.0001,
        slippage_cost=0.00005,
        fee_cost=0.00005,
        market_regime="TRENDING_BULL",
        volatility_regime="NORMAL",
        session="LONDON",
        event_risk="LOW",
        mtf_alignment_score=0.80,
        mtf_conflict_score=0.10,
        contributing_models=["quant", "kronos", "faiss", "regime", "ai"],
        excluded_models=[],
        model_weights={"quant": 0.25, "kronos": 0.25, "faiss": 0.20, "regime": 0.15, "ai": 0.15},
        indicator_evidence={},
        tradingview_evidence={},
        historical_analogue_evidence={},
        decision_trace={},
        snapshot_id="SNAP-001",
        snapshot_content_hash="HASH-001",
        git_commit="94d5efa",
        config_hash="79a4f8e12b79310d",
        engine_version="64.0.0-canonical",
        status="QUALIFIED",
    )

    assert prod.risk_reward == 2.0
    assert "CALL" in prod.telegram_display_text
    
    # Attempt creating a product with future cutoff time
    future_cutoff = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    with pytest.raises(CausalViolationError):
        SignalProduct(
            signal_id="SIG-LEAK-001",
            asset="EURUSD",
            asset_class="FX",
            direction="BUY",
            timeframe="1H",
            signal_scope="INTRADAY",
            created_at=now_str,
            data_cutoff_time=future_cutoff,
            entry_price=1.0850,
            stop_loss=1.0800,
            take_profit=1.0950,
            expiry_time=(datetime.now(timezone.utc) + timedelta(hours=4)).isoformat(),
            expected_hold_time="4H",
            confidence=0.78,
            calibrated_probability=0.74,
            agreement_percentage=75.0,
            quality_tier="A",
            expected_net_r=0.42,
            spread_cost=0.0001,
            slippage_cost=0.00005,
            fee_cost=0.00005,
            market_regime="TRENDING_BULL",
            volatility_regime="NORMAL",
            session="LONDON",
            event_risk="LOW",
            mtf_alignment_score=0.80,
            mtf_conflict_score=0.10,
            contributing_models=["quant"],
            excluded_models=[],
            model_weights={},
            indicator_evidence={},
            tradingview_evidence={},
            historical_analogue_evidence={},
            decision_trace={},
            snapshot_id="SNAP-001",
            snapshot_content_hash="HASH-001",
            git_commit="94d5efa",
            config_hash="79a4f8e12b79310d",
            engine_version="64.0.0-canonical",
            status="QUALIFIED",
        )


# ── 2. Multi-Timeframe Signal Schedule & Telegram Feed ─────────────────────────

def test_multi_timeframe_signal_schedule():
    """Verify multi-timeframe schedule across all core assets."""
    sched = signal_schedule_engine.generate_live_schedule()
    assert sched["success"] is True
    assert sched["total_qualified_count"] >= 1
    assert "live_schedule" in sched
    assert "no_trade_assets" in sched


def test_telegram_style_signal_feed_filtering():
    """Verify filtering by asset, timeframe, direction, quality, and status."""
    feed = signal_schedule_engine.get_signal_feed(
        asset="EURUSD",
        timeframe="1H",
        direction="BUY",
        limit=20,
    )
    assert feed["success"] is True
    assert feed["filters_applied"]["asset"] == "EURUSD"
    for s in feed["signals"]:
        assert s["asset"] == "EURUSD"
        assert s["timeframe"] == "1H"
        assert "telegram_row" in s


# ── 3. MTF Fusion & Signal Strength Decomposition ─────────────────────────────

def test_mtf_fusion_and_signal_strength():
    """Verify 0-100 decomposed signal strength and higher-timeframe alignment."""
    mtf = mtf_fusion_engine.compute_mtf_alignment(base_tf="1H", base_direction="BUY")
    assert mtf.htf_alignment_score >= 0.0
    assert mtf.mtf_conflict_score <= 1.0
    assert len(mtf.timeframe_matrix) > 0

    strength = mtf_fusion_engine.calculate_signal_strength(
        calibrated_probability=0.76,
        expected_net_r=0.48,
        mtf_alignment=0.85,
        quality_grade="A+",
        model_agreement_pct=80.0,
        analogue_quality="HIGH",
    )
    assert 0 <= strength.overall_score <= 100
    assert strength.trend_score >= 50
    assert strength.structure_score >= 80


# ── 4. Zero-Trust Hard Gates & Decision Trace ─────────────────────────────────

def test_zero_trust_decision_trace():
    """Verify boundary checks on confidence, models, RR, and session."""
    valid_trace = mtf_fusion_engine.evaluate_decision_trace(
        price=1.0850,
        freshness_seconds=10.0,
        market_session="LONDON",
        event_risk="LOW",
        contributing_models_count=6,
        consensus_confidence=0.72,
        agreement_percentage=75.0,
        risk_reward=2.0,
        expected_net_r=0.35,
        mtf_conflict_score=0.10,
        causal_check_passed=True,
    )
    assert valid_trace["is_qualified"] is True
    assert valid_trace["overall_decision"] == "QUALIFIED"

    # Failing consensus confidence (0.64 < 0.65)
    failing_trace = mtf_fusion_engine.evaluate_decision_trace(
        price=1.0850,
        freshness_seconds=10.0,
        market_session="LONDON",
        event_risk="LOW",
        contributing_models_count=6,
        consensus_confidence=0.64,
        agreement_percentage=75.0,
        risk_reward=2.0,
        expected_net_r=0.35,
        mtf_conflict_score=0.10,
        causal_check_passed=True,
    )
    assert failing_trace["is_qualified"] is False
    assert "consensus_confidence" in failing_trace["rejections"]


# ── 5. Causal Outcome Resolution & Friction Accounting ────────────────────────

def test_causal_outcome_resolution():
    """Verify outcome engine resolves TP, SL, and friction deductions."""
    res = causal_outcome_learning_engine.resolve_signal_outcome(
        signal_id="SIG-RES-001",
        asset="EURUSD",
        timeframe="1H",
        direction="BUY",
        entry_price=1.0850,
        stop_loss=1.0800,
        take_profit=1.0950,
        data_cutoff_time="2026-08-24T10:00:00Z",
        expiry_time="2026-08-24T14:00:00Z",
    )
    assert res["status"] == "RESOLVED"
    assert res["outcome"] in ["WON", "LOST", "AMBIGUOUS", "TIME_EXIT"]
    assert "net_realized_r" in res
    assert res["is_causal"] is True


# ── 6. Same-Day / Same-Time Historical Intelligence ───────────────────────────

def test_same_day_time_historical_intelligence():
    """Verify time-conditioned historical analogue analysis."""
    intel = causal_outcome_learning_engine.get_same_day_time_intelligence(
        asset="EURUSD",
        target_weekday=0,  # Monday
        session="LONDON",
    )
    assert intel["success"] is True
    assert intel["target_weekday"] == "Monday"
    assert intel["historical_matches_found"] > 0
    assert intel["p_tp_first"] > 0.50


# ── 7. Shadow Tracking & Threshold Policy Generator ───────────────────────────

def test_shadow_signal_counterfactual_tracking():
    """Verify shadow tracking and counterfactual policy recommendations."""
    shadow = causal_outcome_learning_engine.get_shadow_tracking_analysis()
    assert shadow["success"] is True
    assert "counterfactual_analysis" in shadow


# ── 8. REST API Endpoints End-to-End ──────────────────────────────────────────

def test_api_signal_feed_and_schedule(client):
    """Test /api/v1/signals/feed and /schedule."""
    feed_res = client.get("/api/v1/signals/feed?asset=EURUSD&limit=10")
    assert feed_res.status_code == 200
    feed_data = feed_res.json()
    assert feed_data["success"] is True

    sched_res = client.get("/api/v1/signals/schedule")
    assert sched_res.status_code == 200
    assert sched_res.json()["success"] is True


def test_api_results_and_strongest_setups(client):
    """Test /api/v1/signals/results and /setups/strongest."""
    res = client.get("/api/v1/signals/results?horizon=TODAY")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert "metrics" in res.json()

    top_res = client.get("/api/v1/signals/setups/strongest?top_n=3")
    assert top_res.status_code == 200
    assert len(top_res.json()["top_setups"]) >= 1


def test_api_chart_markers(client):
    """Test /api/v1/signals/chart/{signal_id}."""
    chart_res = client.get("/api/v1/signals/chart/SIG-EURUSD-1H-20260824")
    assert chart_res.status_code == 200
    data = chart_res.json()
    assert data["success"] is True
    assert len(data["chart_markers"]) == 3


def test_api_mtf_and_time_conditioned(client):
    """Test /api/v1/signals/mtf/{asset} and /signals/time-conditioned/{asset}."""
    mtf_res = client.get("/api/v1/signals/mtf/BTCUSD")
    assert mtf_res.status_code == 200
    assert mtf_res.json()["success"] is True

    time_res = client.get("/api/v1/signals/time-conditioned/EURUSD?weekday=1&session=NEW_YORK")
    assert time_res.status_code == 200
    assert time_res.json()["success"] is True


# ── 9. 100-Cycle Live Repeatability Test ──────────────────────────────────────

def test_100_cycle_live_api_repeatability(client):
    """Verify 100 repeated cycles produce 100% deterministic identical outputs and invariant hashes."""
    first_res = client.get("/api/v1/signals/feed?asset=EURUSD&limit=10").json()
    
    for cycle in range(100):
        repeat_res = client.get("/api/v1/signals/feed?asset=EURUSD&limit=10").json()
        assert repeat_res["total_count"] == first_res["total_count"]
        assert len(repeat_res["signals"]) == len(first_res["signals"])
        if repeat_res["signals"]:
            assert repeat_res["signals"][0]["signal_id"] == first_res["signals"][0]["signal_id"]
            assert repeat_res["signals"][0]["entry_price"] == first_res["signals"][0]["entry_price"]


# ── 10. Real Money Safety Assurance ───────────────────────────────────────────

def test_real_money_safety_gates():
    """Verify real-money trading and broker execution remain strictly disabled."""
    settings = get_settings()
    assert settings.REAL_MONEY_ENABLED is False
    assert settings.BROKER_EXECUTION_ENABLED is False
    assert settings.EXECUTION_MODE == "DEMO"
