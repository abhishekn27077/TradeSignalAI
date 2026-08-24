"""
tests/test_phase58_5_canonical_pipeline.py
==========================================
Phase 58.5 — Canonical Live Signal Pipeline & Multi-Model Intelligence Verification.

Tests cover all 13 critical requirements:
1. Live refresh & timestamp coherence
2. Canonical runtime identity (Phase 58.5, commit, config hash: 79a4f8e12b79310d)
3. API/UI state consistency across multi-page endpoints
4. FAISS unavailable semantics (explicit UNAVAILABLE, never converted to NEUTRAL)
5. Time pattern / historical sample real calculation
6. Consensus calculation only across valid available evidence
7. Forecast vs qualified trade signal strict separation
8. Duplicate state prevention
9. Granular NO_TRADE reason explainability
10. Multi-page consistency (H4 matrix vs Daily Command vs System Intelligence)
11. Historical phase isolation (no legacy phase labels on live endpoints)
12. Strong signal Zero-Trust qualification policy
13. Strict preservation of all safety rules (Real money strictly disabled)
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.canonical_signal_service import canonical_signal_service, CONFIG_HASH, CORE_ASSETS
from app.config.settings import get_settings


@pytest.fixture
def client():
    return TestClient(app)


# ── 1. Canonical Runtime Identity ─────────────────────────────────────────────

def test_canonical_runtime_identity():
    """Verify runtime identity is canonical Phase 58.5 with config hash 79a4f8e12b79310d."""
    meta = canonical_signal_service.get_canonical_runtime_metadata()
    assert meta["runtime_phase"] == "PHASE 58.5"
    assert meta["config_hash"] == "79a4f8e12b79310d"
    assert meta["runtime_status"] == "CANONICAL_LIVE_SYNCHRONIZED"
    assert meta["real_money_status"] == "STRICTLY_DISABLED"
    assert meta["zero_trust_threshold"] == 0.65
    assert meta["zero_trust_min_rr"] == 1.5


def test_canonical_runtime_api_endpoint(client):
    """Verify GET /api/v1/system-intelligence/canonical-runtime endpoint returns canonical metadata."""
    res = client.get("/api/v1/system-intelligence/canonical-runtime")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["runtime_phase"] == "PHASE 58.5"
    assert data["data"]["config_hash"] == "79a4f8e12b79310d"
    assert data["data"]["real_money_status"] == "STRICTLY_DISABLED"


# ── 2. FAISS Model Availability Semantics ─────────────────────────────────────

def test_faiss_explicit_unavailable_semantics():
    """CRITICAL: UNAVAILABLE must NEVER be converted to NEUTRAL 0%."""
    state = canonical_signal_service.evaluate_asset_intelligence("BTCUSD")
    faiss_m = state["models"]["faiss"]
    
    assert faiss_m["status"] == "UNAVAILABLE"
    assert "reason" in faiss_m
    assert faiss_m["reason"] == "FAISS_VECTOR_INDEX_OFFLINE_PENDING"
    assert faiss_m["direction"] == "UNAVAILABLE"
    assert faiss_m["weight"] == 0.0  # Must not contribute false weight to consensus


# ── 3. Time Pattern Seasonality Calculation ───────────────────────────────────

def test_time_pattern_seasonality_computation():
    """Verify time pattern calculates real day-of-week & session tendencies."""
    dt_monday = datetime(2026, 8, 24, 14, 0, tzinfo=timezone.utc)  # Monday
    state = canonical_signal_service.evaluate_asset_intelligence("EURUSD", dt_monday)
    tp = state["models"]["time_pattern"]
    
    assert tp["status"] == "AVAILABLE"
    assert tp["day_of_week"] == "Monday"
    assert tp["confidence"] > 0.50
    assert tp["direction"] in ["BUY", "SELL", "NEUTRAL"]


# ── 4. Consensus Fusion Across Only Available Models ──────────────────────────

def test_consensus_with_missing_evidence():
    """Consensus must be computed only across AVAILABLE models without false neutral dilution."""
    state = canonical_signal_service.evaluate_asset_intelligence("BTCUSD")
    consensus = state["consensus"]
    
    assert consensus["confidence"] >= 0.50
    assert state["models_available_count"] >= 5
    assert state["models_unavailable_count"] >= 1
    # FAISS is unavailable, so models contributing is available count
    assert consensus["agreement_pct"] > 0.0


# ── 5. Forecast vs Qualified Signal Strict Separation ─────────────────────────

def test_forecast_vs_qualified_signal_distinction():
    """Forecast confidence does NOT automatically equal trade qualification."""
    # When market is closed for forex on weekend, forecast exists but trade is gated
    dt_weekend = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)  # Sunday noon UTC (forex closed)
    state = canonical_signal_service.evaluate_asset_intelligence("EURUSD", dt_weekend)
    
    # Forecast is computed
    assert state["direction"] in ["BUY", "SELL", "NEUTRAL"]
    assert state["forecast_confidence"] > 0.0
    # But trade signal is gated closed
    assert state["is_market_open"] is False
    assert state["is_trade_signal_qualified"] is False
    assert state["qualification_status"] == "NO_TRADE"
    assert state["qualification_reason"] == "MARKET_CLOSED"
    assert state["signal_id"] is None


# ── 6. Strong Signal Qualification Policy ─────────────────────────────────────

def test_strong_signal_qualification_policy():
    """Strong signals require all Zero-Trust criteria: Open, Conf >= 0.65, Models >= 5, RR >= 1.5."""
    # Crypto (BTCUSD) is 24/7 open
    now_utc = datetime.now(timezone.utc)
    state = canonical_signal_service.evaluate_asset_intelligence("BTCUSD", now_utc)
    
    assert state["is_market_open"] is True
    assert state["risk_reward"] >= 1.5
    assert state["models_available_count"] >= 5
    
    if state["forecast_confidence"] >= 0.65 and state["agreement_pct"] >= 60.0:
        assert state["is_trade_signal_qualified"] is True
        assert state["signal_classification"] in ["STRONG_BUY", "STRONG_SELL"]
        assert state["qualification_status"] == "QUALIFIED"
        assert state["signal_id"] is not None
    else:
        assert state["is_trade_signal_qualified"] is False


# ── 7. Granular NO_TRADE Reason Explainability ────────────────────────────────

def test_granular_no_trade_reasons():
    """Every non-qualified asset must present a precise, actionable disqualification reason."""
    all_states = canonical_signal_service.get_all_canonical_asset_states()
    for st in all_states:
        if not st["is_trade_signal_qualified"]:
            assert st["qualification_reason"] in [
                "MARKET_CLOSED",
                "HIGH_EVENT_RISK",
                "CONSENSUS_BELOW_THRESHOLD",
                "INSUFFICIENT_MODEL_EVIDENCE",
                "DIRECTIONAL_BIAS_PENDING_CONFIRMATION",
            ]


# ── 8. Multi-Page State Consistency (H4 Matrix vs Daily Command vs System Intel)

def test_multi_page_state_consistency(client):
    """Verify that H4 Matrix, Daily Command, and System Intelligence return identical states."""
    h4_res = client.get("/api/v1/signals/h4-intelligence").json()
    daily_res = client.get("/api/v1/live/today").json()
    sys_res = client.get("/api/v1/system-intelligence/canonical-signals").json()
    
    assert h4_res["success"] is True
    assert "matrix" in h4_res
    assert len(h4_res["matrix"]) == 9
    
    assert "forecasts" in daily_res
    assert len(daily_res["forecasts"]) == 9
    
    assert sys_res["success"] is True
    assert len(sys_res["data"]) == 9
    
    # Verify identical direction and asset matching across all 9 assets
    for i, asset in enumerate(CORE_ASSETS):
        h4_item = next(m for m in h4_res["matrix"] if m["asset"] == asset)
        daily_item = next(f for f in daily_res["forecasts"] if f["asset"] == asset)
        sys_item = next(s for s in sys_res["data"] if s["asset"] == asset)
        
        assert h4_item["consensus"] == daily_item["direction"] == sys_item["direction"]
        assert h4_item["price"] == daily_item["entry_price"] == sys_item["price"]
        assert h4_item["risk_reward"] == daily_item["risk_reward"] == sys_item["risk_reward"]


# ── 9. Historical Phase Isolation ─────────────────────────────────────────────

def test_historical_phase_isolation(client):
    """Verify live status endpoints return Phase 58.5 canonical cohort and no legacy phase pollution."""
    res = client.get("/api/v1/live/status")
    assert res.status_code == 200
    data = res.json()
    
    assert data["runtime_phase"] == "PHASE 58.5"
    assert data["config_hash"] == "79a4f8e12b79310d"
    assert data["validation_cohort"] == "PHASE_58_5_CANONICAL_COHORT"
    assert data["system_status"] == "LIVE"
    assert data["real_money_execution"] == "DISABLED_SAFETY_ENFORCED"


# ── 10. Duplicate State Prevention & Idempotency ──────────────────────────────

def test_duplicate_state_prevention():
    """Verify repeated evaluations on identical point-in-time yield identical deterministic results."""
    dt = datetime(2026, 8, 24, 10, 0, 0, tzinfo=timezone.utc)
    res_a = canonical_signal_service.evaluate_asset_intelligence("BTCUSD", dt)
    res_b = canonical_signal_service.evaluate_asset_intelligence("BTCUSD", dt)
    
    assert res_a["direction"] == res_b["direction"]
    assert res_a["forecast_confidence"] == res_b["forecast_confidence"]
    assert res_a["is_trade_signal_qualified"] == res_b["is_trade_signal_qualified"]
    assert res_a["qualification_reason"] == res_b["qualification_reason"]


# ── 11. Live Timestamp Coherence ──────────────────────────────────────────────

def test_live_timestamp_coherence():
    """Verify all runtime timestamp fields are present and valid ISO-8601 strings."""
    meta = canonical_signal_service.get_canonical_runtime_metadata()
    ts_fields = ["last_market_data_at", "last_forecast_at", "last_consensus_at", "last_qualification_at", "last_ui_sync_at"]
    
    for f in ts_fields:
        assert f in meta
        # Validate parseable ISO format
        dt = datetime.fromisoformat(meta[f])
        assert dt is not None


# ── 12. Real Money Hard Safety Lockout ────────────────────────────────────────

def test_real_money_hard_safety_lockout():
    """Verify execution mode is strictly DEMO and real money execution is blocked."""
    settings = get_settings()
    assert settings.EXECUTION_MODE in ["DEMO", "PAPER"]
    meta = canonical_signal_service.get_canonical_runtime_metadata()
    assert meta["real_money_status"] == "STRICTLY_DISABLED"


# ── 13. All 9 Core Assets Evaluated ───────────────────────────────────────────

def test_all_nine_core_assets_evaluated():
    """Verify all 9 assets (EURUSD, GBPUSD, USDJPY, AUDUSD, BTCUSD, ETHUSD, XAUUSD, NAS100, SPX500) are evaluated."""
    states = canonical_signal_service.get_all_canonical_asset_states()
    evaluated_symbols = [s["asset"] for s in states]
    assert len(evaluated_symbols) == 9
    for sym in CORE_ASSETS:
        assert sym in evaluated_symbols
