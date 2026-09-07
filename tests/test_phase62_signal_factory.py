"""
tests/test_phase62_signal_factory.py
====================================
Test suite for Multi-Timeframe Signal Factory, Signal Stream & Daily Signal Book APIs.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.signal_factory import signal_factory, SUPPORTED_TIMEFRAMES, CORE_ASSETS
from app.analytics.champion_challenger_engine import champion_challenger_engine


@pytest.fixture
def client():
    return TestClient(app)


# ── 1. Multi-Timeframe Signal Generation ──────────────────────────────────────

@pytest.mark.parametrize("tf", SUPPORTED_TIMEFRAMES)
def test_signal_factory_multi_timeframe_generation(tf):
    """Verify signal factory independently generates signals for each supported timeframe."""
    sig = signal_factory.generate_signal("BTCUSD", tf)
    assert sig.asset == "BTCUSD"
    assert sig.timeframe == tf
    assert sig.risk_reward >= 1.50
    assert sig.calibrated_probability > 0.0
    assert sig.p_tp_first + sig.p_sl_first + sig.p_time_exit > 0.99
    assert sig.quality_grade in ["A+", "A", "B", "C", "WATCH", "REJECTED"]
    assert "price_validity" in sig.decision_trace


# ── 2. Signal Quality Tiers & Risk Gating ─────────────────────────────────────

def test_signal_quality_high_event_risk_rejection():
    """Verify high event risk forces signal to REJECTED."""
    sig = signal_factory.generate_signal("EURUSD", "1H")
    assert sig.event_risk in ["LOW", "MEDIUM", "HIGH"]
    if sig.event_risk == "HIGH":
        assert sig.status == "REJECTED"
        assert sig.decision == "NO_TRADE"


# ── 3. API Route: /signals/stream ─────────────────────────────────────────────

def test_api_signals_stream(client):
    """Verify /signals/stream returns properly formatted chronological signals."""
    res = client.get("/api/v1/signals/stream?limit=20")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["signals"]) > 0

    first = data["signals"][0]
    assert "signal_id" in first
    assert "calibrated_probability" in first
    assert "expected_net_r" in first
    assert "quality_grade" in first
    assert "consensus_agreement" in first


# ── 4. API Route: /signals/book ───────────────────────────────────────────────

def test_api_daily_signal_book(client):
    """Verify /signals/book returns multi-timeframe book and yesterday results."""
    res = client.get("/api/v1/signals/book")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    book = data["data"]
    assert "date" in book
    assert "total_signals_generated" in book
    assert "yesterday_results" in book
    assert "by_asset" in book
    for sym in CORE_ASSETS:
        assert sym in book["by_asset"]


# ── 5. API Route: /signals/indicators ─────────────────────────────────────────

def test_api_indicator_catalog(client):
    """Verify /signals/indicators returns registered indicators and clusters."""
    res = client.get("/api/v1/signals/indicators")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["total_registered"] >= 10
    for ind in data["indicators"]:
        assert "cluster" in ind
        assert "non_repainting" in ind


# ── 6. API Route: /signals/analogues ──────────────────────────────────────────

def test_api_historical_analogues(client):
    """Verify /signals/analogues/:asset/:timeframe returns analogue distributions."""
    res = client.get("/api/v1/signals/analogues/BTCUSD/4H?direction=BUY&regime=TRENDING_BULL")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    report = data["data"]
    assert report["asset"] == "BTCUSD"
    assert report["timeframe"] == "4H"
    assert "forward_distributions" in report
    assert "4H" in report["forward_distributions"]


# ── 7. API Route: /signals/champion-challenger ────────────────────────────────

def test_api_champion_challenger_scorecard(client):
    """Verify /signals/champion-challenger returns side-by-side model matrix."""
    res = client.get("/api/v1/signals/champion-challenger")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    matrix = data["data"]
    assert "active_champion_id" in matrix
    assert len(matrix["models"]) >= 3


# ── 8. API Route: /signals/ablation ───────────────────────────────────────────

def test_api_model_ablation(client):
    """Verify /signals/ablation returns marginal alpha contribution per configuration."""
    res = client.get("/api/v1/signals/ablation")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["benchmarks"]) >= 4


# ── 9. API Route: /signals/replay ─────────────────────────────────────────────

def test_api_walk_forward_replay(client):
    """Verify POST /signals/replay executes walk-forward simulation."""
    res = client.post("/api/v1/signals/replay?asset=BTCUSD&timeframe=4H&bars_back=30")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data_boundary_status"] == "ZERO_LOOKAHEAD_VERIFIED"
    assert data["lookahead_violations_detected"] == 0


# ── 10. Performance Mathematical Reconciliation ───────────────────────────────

def test_mathematical_performance_reconciliation():
    """Verify individual trade Net R sum exactly equals total reported Net R."""
    book = signal_factory.get_daily_signal_book()
    yest = book["yesterday_results"]
    trades = yest["trades"]
    sum_individual = round(sum(t["net_r"] for t in trades), 2)
    assert sum_individual == yest["total_net_r"]
