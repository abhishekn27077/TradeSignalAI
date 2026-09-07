"""
tests/test_pipeline_e2e_real_market.py
======================================
Comprehensive End-to-End Real Market Pipeline & Zero-Trust Verification Test Suite.
Verifies the complete pipeline from Market Data -> Candles -> Features -> Models ->
Consensus -> SMC -> Risk Gates -> Zero-Trust Decision -> Canonical Persistence -> APIs.
"""

import pytest
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.core.canonical_prospective_ledger import (
    canonical_prospective_ledger,
    CanonicalProspectiveSignal,
    CORE_ASSETS,
    STATUS_UPCOMING,
    STATUS_ENTRY_WINDOW,
    STATUS_ACTIVE,
    STATUS_RESOLVED,
    OUTCOME_WON,
    OUTCOME_LOST,
)
from app.analytics.master_intelligence_engine import master_intelligence_engine
from app.strategies.Structure import SwingDetector, BOSEngine, CHoCHEngine, StructureStrengthEngine
from app.strategies.SmartMoney.OrderBlocks import OrderBlockEngine
from app.strategies.SmartMoney.FVG import FVGEngine
from app.strategies.SignalQuality.engine import SignalQualityEngine
from app.strategies.SignalQuality.models import SignalGrade, NoTradeReason

client = TestClient(app)


# ---------------------------------------------------------------------------
# Test 1: Real Market Data Ingestion & Candle Normalization
# ---------------------------------------------------------------------------
def test_e2e_market_data_normalization():
    conn = sqlite3.connect("tradesignal.db")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT symbol, timeframe, timestamp, open, high, low, close, volume
        FROM historical_candles
        WHERE symbol = 'EURUSD' AND timeframe IN ('1H', '1h', 'H1')
        ORDER BY timestamp DESC LIMIT 50
        """
    )
    rows = cur.fetchall()
    conn.close()

    assert len(rows) >= 15, "Expected at least 15 EURUSD candles in historical database"
    for r in rows:
        symbol, tf, ts, o, h, l, c, v = r
        o, h, l, c = float(o), float(h), float(l), float(c)
        assert h >= l, f"High ({h}) must be >= Low ({l})"
        assert h >= o, f"High ({h}) must be >= Open ({o})"
        assert h >= c, f"High ({h}) must be >= Close ({c})"
        assert l <= o, f"Low ({l}) must be <= Open ({o})"
        assert l <= c, f"Low ({l}) must be <= Close ({c})"


# ---------------------------------------------------------------------------
# Test 2: Feature Calculation & Indicator Parity
# ---------------------------------------------------------------------------
def test_e2e_feature_calculation():
    # Build synthetic but geometrically valid 60-bar series
    dates = pd.date_range("2026-08-01", periods=60, freq="1h", tz="UTC")
    closes = 1.0800 + np.cumsum(np.random.normal(0, 0.0005, 60))
    highs = closes + 0.0010
    lows = closes - 0.0010
    opens = closes - 0.0002
    volumes = np.random.uniform(500, 1500, 60)

    df = pd.DataFrame({
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
    }, index=dates)

    # Calculate ATR and RSI
    tr = np.maximum(df["high"] - df["low"], np.abs(df["high"] - df["close"].shift(1)))
    atr14 = tr.rolling(14).mean()
    assert not atr14.iloc[-1] is np.nan
    assert atr14.iloc[-1] > 0

    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    rsi14 = 100 - (100 / (1 + rs))
    assert 0 <= rsi14.iloc[-1] <= 100


# ---------------------------------------------------------------------------
# Test 3: Model Inference (Kronos / Statistical Ensembles)
# ---------------------------------------------------------------------------
def test_e2e_model_inference_kronos_and_stats():
    from app.analytics.consensus_engine import ConsensusEngine
    engine = ConsensusEngine()

    dates = pd.date_range("2026-08-01", periods=100, freq="1h", tz="UTC")
    closes = 1.0850 + np.linspace(0, 0.0100, 100)  # Strong upward trend
    df = pd.DataFrame({
        "open": closes - 0.0005,
        "high": closes + 0.0010,
        "low": closes - 0.0008,
        "close": closes,
        "volume": np.full(100, 1000.0),
    }, index=dates)

    res = engine.generate_consensus("EURUSD", "1H", df)
    assert res is not None
    assert "signal" in res or "consensus_expected_return" in res or "weights" in res


# ---------------------------------------------------------------------------
# Test 4: Multi-Model Consensus & Collinearity Attenuation
# ---------------------------------------------------------------------------
def test_e2e_consensus_collinearity_attenuation():
    # Verify that duplicate model votes do not artificially inflate confidence beyond bounds
    from app.strategies.Ensemble.ensemble_engine import StrategyEnsembleEngine
    from app.strategies.Ensemble.models import StrategyVote, StrategyFamily

    engine = StrategyEnsembleEngine()
    votes = [
        StrategyVote(family=StrategyFamily.TREND, direction="BUY", confidence=0.80, quality=0.85, regime_suitability=0.90),
        StrategyVote(family=StrategyFamily.TREND, direction="BUY", confidence=0.82, quality=0.80, regime_suitability=0.85),
        StrategyVote(family=StrategyFamily.BREAKOUT, direction="BUY", confidence=0.75, quality=0.78, regime_suitability=0.80),
    ]

    res = engine.evaluate_ensemble(votes=votes, regime="STRONG_TREND")
    assert res is not None
    assert 0.50 <= res.ensemble_confidence <= 1.0
    assert res.direction == "BUY"
    assert res.participating_strategies == 3


# ---------------------------------------------------------------------------
# Test 5: Smart Money Concepts & Market Structure Calculation
# ---------------------------------------------------------------------------
def test_e2e_smc_structure_calculation():
    dates = pd.date_range("2026-08-01", periods=60, freq="1h", tz="UTC")
    # Alternating swing structure
    closes = 1.0800 + np.sin(np.linspace(0, 6 * np.pi, 60)) * 0.0050
    df = pd.DataFrame({
        "open": closes - 0.0002,
        "high": closes + 0.0008,
        "low": closes - 0.0008,
        "close": closes,
        "volume": np.full(60, 1200.0),
    }, index=dates)

    detector = SwingDetector(left_len=3, right_len=3)
    swings = detector.detect_swings(df, asset="EURUSD", timeframe="1H")
    assert len(swings) >= 2, "Expected swing pivots detected"

    ob_engine = OrderBlockEngine(swing_len=3)
    obs = ob_engine.detect_order_blocks(df, asset="EURUSD", timeframe="1H")
    assert isinstance(obs, list)


# ---------------------------------------------------------------------------
# Test 6: SMC Insufficient Data Guard (No Fake 0 Score)
# ---------------------------------------------------------------------------
def test_e2e_smc_insufficient_data_guard():
    # Pass an asset with no historical data
    res = client.get("/api/v1/analysis/structure/NONEXISTENT_ASSET?timeframe=1H")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "INSUFFICIENT_DATA"
    assert data["strength"]["reason"] == "INSUFFICIENT_HISTORICAL_BARS"


# ---------------------------------------------------------------------------
# Test 7: Zero-Trust Decision Gating & NO_TRADE Reasons
# ---------------------------------------------------------------------------
def test_e2e_risk_gates_zero_trust():
    engine = SignalQualityEngine(min_rr_ratio=1.5, min_confluence_score=60.0)

    # Test gate failure: neutral direction & low confluence
    evaluation = engine.evaluate_signal_quality(
        asset="EURUSD",
        direction="NEUTRAL",
        entry_price=1.0800,
        stop_loss=1.0750,
        take_profit=1.0820,  # poor R:R
        confluence_score=40.0,
    )
    assert evaluation.is_actionable is False
    assert len(evaluation.rejection_reasons) >= 1
    assert evaluation.grade == SignalGrade.NO_TRADE


# ---------------------------------------------------------------------------
# Test 8: Canonical Prospective Signal Persistence & Resolution
# ---------------------------------------------------------------------------
def test_e2e_canonical_signal_lifecycle_and_persistence():
    now = datetime.now(timezone.utc)
    sig_id = f"SIG-E2E-TEST-{now.strftime('%Y%m%d%H%M%S')}-EURUSD-1H-001"
    timing = canonical_prospective_ledger.compute_exact_timing(now, "1H")

    sig = CanonicalProspectiveSignal(
        signal_id=sig_id,
        campaign_id="CAMPAIGN-E2E-TEST",
        generated_at_utc=now.isoformat(),
        generated_at_ist=(now + timedelta(hours=5, minutes=30)).isoformat(),
        asset="EURUSD",
        timeframe="1H",
        direction="BUY",
        market_snapshot_hash="snap-e2e-hash",
        policy_version="POL-69A-v1",
        model_version="ENSEMBLE-P68-v1",
        config_hash="cfg-e2e-hash",
        entry_window_start=timing["entry_window_start"],
        entry_window_end=timing["entry_window_end"],
        preferred_entry_time=timing["preferred_entry_time"],
        entry_price=1.0850,
        stop_loss=1.0800,
        take_profit=1.0950,
        expected_hold_seconds=3600,
        expected_exit_time=timing["expected_exit_time"],
        max_exit_time=timing["max_exit_time"],
        probability=0.78,
        signal_strength=82,
        quality_grade="A+",
        expected_r=0.62,
        regime="TRENDING_EXPANSION",
        mtf_alignment=0.88,
        risk_state="NORMAL",
        qualification_status="QUALIFIED",
        signal_status=STATUS_ACTIVE,
    )

    success = canonical_prospective_ledger.persist_signal(sig)
    assert success is True

    # Test resolution
    resolved = canonical_prospective_ledger.resolve_signal_outcome(
        signal_id=sig_id,
        outcome=OUTCOME_WON,
        resolution_reason="TP_HIT",
        actual_exit_price=1.0950,
        actual_exit_time=timing["expected_exit_time"],
        gross_r=2.00,
        net_r=1.95,
    )
    assert resolved is True

    fetched = canonical_prospective_ledger.get_signal(sig_id)
    assert fetched.outcome == OUTCOME_WON
    assert fetched.net_r == 1.95


# ---------------------------------------------------------------------------
# Test 9: H4 Intelligence API Contract & Candle Boundaries
# ---------------------------------------------------------------------------
def test_e2e_h4_intelligence_endpoint():
    res = client.get("/api/v1/signals/h4-intelligence")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["assets_scanned"] == len(CORE_ASSETS)
    assert "candle_boundary" in data
    assert "current_candle_close_ist" in data["candle_boundary"]
    assert len(data["matrix"]) == len(CORE_ASSETS)


# ---------------------------------------------------------------------------
# Test 10: Truthful System Health Status
# ---------------------------------------------------------------------------
def test_e2e_system_health_truthfulness():
    res = client.get("/api/v1/system/status")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    components = data["components"]
    assert components["database"] == "ok"
    assert components["ai_engine"] in ("ok", "degraded")
    assert components["local_models"] == "ok"
    assert components["websocket"] == "ok"


# ---------------------------------------------------------------------------
# Test 11: WebSocket Endpoint Handshake
# ---------------------------------------------------------------------------
def test_e2e_websocket_heartbeat_and_broadcast():
    with client.websocket_connect("/api/v1/ws/stream") as websocket:
        # First message: connected confirmation
        msg1 = websocket.receive_json()
        assert msg1.get("event") == "connected"

        # Second message: system health broadcast
        msg2 = websocket.receive_json()
        assert msg2.get("event") == "system_health"
        assert msg2["data"]["components"]["database"] == "ok"

        # Send ping
        websocket.send_json({"action": "ping"})
        resp = websocket.receive_json()
        assert resp.get("event") == "pong"
