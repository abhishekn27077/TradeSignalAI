"""
tests/test_phase63_real_data_validation.py
==========================================
Comprehensive Automated Test Suite for Phase 63:
Real-Data Validation, TradingView MCP Live Intelligence & Causal Signal Truth Engine.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import sqlite3
import os

from app.main import app
from app.market_intelligence.tradingview_adapter import tradingview_adapter
from app.analytics.historical_analog_engine import historical_analog_engine
from app.analytics.confidence_calibration import confidence_calibration_engine
from app.analytics.indicator_ablation import indicator_ablation_engine
from app.analytics.baseline_competition import baseline_competition_engine
from app.analytics.multiple_testing_registry import multiple_testing_registry
from app.core.signal_factory import signal_factory
from app.core.signal_pipeline import signal_pipeline


@pytest.fixture
def client():
    return TestClient(app)


# ── 1. TradingView Capability Matrix & Provenance ─────────────────────────────

def test_tradingview_capability_matrix_honest_reporting():
    """Verify TradingView capability matrix honestly reports structured OHLCV and offline visual status."""
    caps = tradingview_adapter.capability_matrix
    assert caps["structured_ohlcv_available"] is True
    assert caps["pinescript_parity_verified"] is True
    assert caps["visual_chart_screenshots_available"] is False
    
    # Check individual capability definitions
    cap_names = [c["name"] for c in caps["capabilities"]]
    assert "structured_ohlcv" in cap_names
    assert "pinescript_indicators" in cap_names
    assert "chart_screenshots" in cap_names


def test_tradingview_signal_provenance_metadata():
    """Verify all extracted observations carry complete tamper-evident provenance metadata."""
    obs = tradingview_adapter.extract_indicator_observations("EURUSD", "1H")
    assert len(obs.provenance_records) > 0
    prov = obs.provenance_records[0]
    assert prov.source == "tvDatafeed_Native_Engine"
    assert prov.symbol == "EURUSD"
    assert prov.timeframe == "1H"
    assert prov.repainting_status == "STRICTLY_NON_REPAINTING"
    assert prov.lookahead_status == "ZERO_LOOKAHEAD_VERIFIED"


# ── 2. Historical Analogue Real SQLite Matching & Episode Clustering ──────────

def test_historical_analogues_real_sqlite_and_episode_clustering():
    """Verify Historical Analogue engine clusters overlapping windows and computes quality score."""
    t0 = datetime(2026, 8, 24, 12, 0, 0, tzinfo=timezone.utc)
    report = historical_analog_engine.find_analogues("BTCUSD", "4H", {"regime": "TRENDING_BULL", "direction": "BUY"}, dt_utc=t0)
    
    assert report.raw_analogue_count >= report.independent_episodes_count
    assert report.independent_episodes_count > 0
    assert report.analogue_quality in ["HIGH", "MEDIUM", "LOW"]
    assert "independent_episodes_sample" in report.sample_breakdown
    assert len(report.top_matches) > 0


# ── 3. Point-in-Time Signal Reproducibility ───────────────────────────────────

def test_point_in_time_signal_reproducibility():
    """Verify that recreating a signal at historical timestamp T0 produces 100% deterministic identical outputs."""
    t0 = datetime(2026, 8, 20, 14, 30, 0, tzinfo=timezone.utc)
    sig_1 = signal_factory.generate_signal("EURUSD", "1H", dt_utc=t0)
    sig_2 = signal_factory.generate_signal("EURUSD", "1H", dt_utc=t0)
    
    assert sig_1.signal_id == sig_2.signal_id
    assert sig_1.direction == sig_2.direction
    assert sig_1.entry_price == sig_2.entry_price
    assert sig_1.calibrated_probability == sig_2.calibrated_probability
    assert sig_1.expected_net_r == sig_2.expected_net_r


# ── 4. Data Freshness Gate ────────────────────────────────────────────────────

def test_data_freshness_gate():
    """Verify that feeds older than 30 seconds are rejected with STALE_DATA_BLOCKED."""
    fresh_check = signal_pipeline.check_data_freshness(staleness_seconds=12.5)
    assert fresh_check["passed"] is True
    assert fresh_check["status"] == "FRESH"

    stale_check = signal_pipeline.check_data_freshness(staleness_seconds=45.0)
    assert stale_check["passed"] is False
    assert stale_check["status"] == "STALE_DATA_BLOCKED"


# ── 5. Confidence Calibration 9-Bin Audit ─────────────────────────────────────

def test_confidence_calibration_9_bins_and_brier_score():
    """Verify confidence calibration across all 9 probability bins, Brier score, and ECE."""
    audit = confidence_calibration_engine.compute_calibration_audit()
    assert len(audit["calibration_bins"]) == 9
    assert audit["overall_brier_score"] < 0.25
    assert audit["expected_calibration_error_ece"] < 0.05
    assert audit["is_well_calibrated"] is True


# ── 6. Indicator Ablation & Correlation ───────────────────────────────────────

def test_indicator_ablation_and_cluster_correlation():
    """Verify leave-one-out indicator ablation and intra-cluster correlation matrix."""
    ablation = indicator_ablation_engine.run_indicator_ablation()
    assert len(ablation["ablation_results"]) >= 6
    for res in ablation["ablation_results"]:
        assert res["classification"] in ["HELPFUL", "NEUTRAL", "HARMFUL", "INSUFFICIENT_SAMPLE"]
    assert "matrix" in ablation["correlation_matrix"]
    assert len(ablation["correlation_matrix"]["high_correlation_pairs"]) >= 1


# ── 7. Baseline Benchmark Competition ─────────────────────────────────────────

def test_baseline_benchmark_competition():
    """Verify TradeSignalAI consensus outperforms naive baselines after friction deductions."""
    comp = baseline_competition_engine.run_baseline_competition()
    assert comp["transaction_frictions_included"]["spread_deducted"] is True
    assert len(comp["benchmarks"]) >= 5
    
    top = comp["benchmarks"][0]
    assert top["strategy_name"] == "TradeSignalAI-v3 Full Consensus"
    assert top["edge_status"] == "OUTPERFORMS_ALL_BASELINES"
    assert top["expectancy_r"] > 0.10


# ── 8. Multiple Testing Experiment Registry ───────────────────────────────────

def test_multiple_testing_registry():
    """Verify experiment logging and holdout protection status."""
    reg = multiple_testing_registry.get_registry_summary()
    assert reg["total_experiments_logged"] >= 2
    assert reg["holdout_protection_status"] == "STRICTLY_LOCKED"


# ── 9. API Routes End-to-End Testing ──────────────────────────────────────────

def test_api_capabilities(client):
    """Test GET /api/v1/signals/capabilities."""
    res = client.get("/api/v1/signals/capabilities")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["structured_ohlcv_available"] is True


def test_api_monitor(client):
    """Test GET /api/v1/signals/monitor."""
    res = client.get("/api/v1/signals/monitor")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["overall_health"] in ["HEALTHY", "DEGRADED"]


def test_api_calibration(client):
    """Test GET /api/v1/signals/calibration."""
    res = client.get("/api/v1/signals/calibration")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "overall_brier_score" in data["data"]


def test_api_indicator_ablation(client):
    """Test GET /api/v1/signals/indicator-ablation."""
    res = client.get("/api/v1/signals/indicator-ablation")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["data"]["ablation_results"]) >= 6


def test_api_baselines(client):
    """Test GET /api/v1/signals/baselines."""
    res = client.get("/api/v1/signals/baselines")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["data"]["benchmarks"]) >= 5


def test_api_edge_status(client):
    """Test GET /api/v1/signals/edge-status."""
    res = client.get("/api/v1/signals/edge-status")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    edge = data["data"]
    assert edge["real_money_trading"] == "STRICTLY_DISABLED"
    assert edge["sample_adequacy"] == "SUFFICIENT"


def test_api_point_in_time_replay(client):
    """Test POST /api/v1/signals/point-in-time-replay."""
    res = client.post("/api/v1/signals/point-in-time-replay?asset=EURUSD&timeframe=1H&historical_timestamp_iso=2026-08-20T13:00:00Z")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["is_reproducible"] is True
    assert "reproduced_signal" in data
