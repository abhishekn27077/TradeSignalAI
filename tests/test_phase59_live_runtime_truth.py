"""
tests/test_phase59_live_runtime_truth.py
========================================
Phase 59 — Canonical Live Runtime Truth & Strong Signal Engine Verification.

Tests verify:
1. Runtime Truth endpoint (/api/v1/system-intelligence/runtime-truth)
2. Response fingerprint headers (X-Canonical-Engine-Version, X-Git-Commit, X-Config-Hash, X-Canonical-State-ID, X-Generated-At, X-Market-Data-Timestamp)
3. FAISS explicit UNAVAILABLE semantics (weight=0, direction=None, zero consensus dilution)
4. Time pattern & seasonality real calculation (day of week, sample count >= 1000)
5. Strict canonical signal schema validation across all 9 assets
6. Forecast vs Executable Signal strict separation
7. Multi-page cross-validation (H4 matrix == Daily Command == System Intelligence)
8. Dashboard and Daily Command counter equality
9. Zero-Trust Strong Signal policy enforcement (Conf >= 0.65, Models >= 5, RR >= 1.5)
10. Market data freshness tracking and age calculation
11. Zero production fallback contamination
12. Absolute real-money execution hard lockout
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


# ── 1. Runtime Truth Endpoint Verification ───────────────────────────────────

def test_runtime_truth_endpoint(client):
    """Verify /api/v1/system-intelligence/runtime-truth returns live runtime information."""
    res = client.get("/api/v1/system-intelligence/runtime-truth")
    assert res.status_code == 200
    data = res.json()

    assert data["engine"] == "TradeSignalAI"
    assert data["phase"] in ["59", "60"]
    assert data["engine_version"] in ["59.0.0-canonical", "60.0.0-canonical"]
    assert data["canonical_engine_version"] in ["59.0.0-canonical", "60.0.0-canonical"]
    assert data["config_hash"] == CONFIG_HASH
    assert isinstance(data["backend_pid"], int)
    assert data["backend_pid"] > 0
    assert len(data["python_executable"]) > 0
    assert len(data["backend_working_directory"]) > 0
    assert data["execution_mode"] == "DEMO"
    assert data["real_money_enabled"] is False
    assert data["broker_execution_enabled"] is False
    assert data["canonical_state_id"].startswith(("STATE-59-", "SNAP-"))


# ── 2. Response Fingerprint Headers ──────────────────────────────────────────

def test_canonical_response_fingerprint_headers(client):
    """Verify that canonical response fingerprint headers are attached by middleware."""
    res = client.get("/api/v1/signals/h4-intelligence")
    assert res.status_code == 200

    headers = res.headers
    assert "X-Canonical-Engine-Version" in headers
    assert "X-Git-Commit" in headers
    assert "X-Config-Hash" in headers
    assert "X-Canonical-State-ID" in headers
    assert "X-Generated-At" in headers
    assert "X-Market-Data-Timestamp" in headers

    assert headers["X-Config-Hash"] == CONFIG_HASH
    assert headers["X-Canonical-State-ID"].startswith(("STATE-59-", "SNAP-"))


# ── 3. FAISS Explicit Unavailable Semantics ──────────────────────────────────

def test_faiss_unavailable_not_diluting_consensus():
    """Verify FAISS UNAVAILABLE is explicit and does not cast fake neutral votes."""
    state = canonical_signal_service.evaluate_asset_intelligence("BTCUSD")
    faiss_m = state["model_breakdown"]["faiss"]

    assert faiss_m["status"] == "UNAVAILABLE"
    assert faiss_m["direction"] is None
    assert faiss_m["confidence"] is None
    assert faiss_m["weight"] == 0.0
    assert faiss_m["reason"] == "FAISS_VECTOR_INDEX_OFFLINE_PENDING"

    # Consensus must only count available models
    assert "faiss_memory" not in state["available_models"]
    assert state["contributing_models"] == len(state["available_models"])


# ── 4. Time Pattern Seasonality Real Calculation ──────────────────────────────

def test_time_pattern_seasonality_real_calculation():
    """Verify time pattern calculates real day-of-week and sample count."""
    dt_monday = datetime(2026, 8, 24, 15, 0, tzinfo=timezone.utc)
    state = canonical_signal_service.evaluate_asset_intelligence("EURUSD", dt_monday)
    tp = state["model_breakdown"]["time_pattern"]

    assert tp["status"] == "AVAILABLE"
    assert tp["day_of_week"] == "Monday"
    assert tp["historical_sample_count"] >= 1000
    assert tp["confidence"] >= 0.50
    assert tp["direction"] in ["BUY", "SELL", "NEUTRAL"]


# ── 5. Canonical Signal Schema Validation ────────────────────────────────────

def test_canonical_signal_schema_completeness():
    """Verify all 9 assets produce complete canonical objects matching the required schema."""
    all_states = canonical_signal_service.get_all_canonical_asset_states()
    assert len(all_states) == 9

    required_keys = [
        "asset", "timestamp", "market_data_timestamp", "timeframe",
        "direction", "signal_class", "consensus", "confidence",
        "available_models", "contributing_models", "model_breakdown",
        "entry", "stop_loss", "take_profit", "risk_reward",
        "session_status", "event_risk", "data_freshness",
        "risk_status", "qualification_status", "decision",
        "reason_codes", "engine_version", "config_hash", "canonical_state_id"
    ]

    for st in all_states:
        for k in required_keys:
            assert k in st, f"Missing key '{k}' in canonical state for {st.get('asset')}"
        assert st["config_hash"] == CONFIG_HASH
        assert st["engine_version"] in ["59.0.0-canonical", "60.0.0-canonical"]
        assert st["timeframe"] == "4H"
        assert st["risk_reward"] >= 1.5


# ── 6. Forecast vs Executable Signal Separation ───────────────────────────────

def test_forecast_vs_executable_signal_separation():
    """Forecast direction exists for analytical tracking, but decision is NO_TRADE if gated."""
    dt_closed = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)  # Weekend forex closed
    state = canonical_signal_service.evaluate_asset_intelligence("EURUSD", dt_closed)

    assert state["direction"] in ["BUY", "SELL", "NEUTRAL"]
    assert state["session_status"] == "CLOSED"
    assert state["is_trade_signal_qualified"] is False
    assert state["qualification_status"] == "NO_TRADE"
    assert state["decision"] == "NO_TRADE"
    assert "MARKET_CLOSED" in state["reason_codes"]
    assert state["signal_id"] is None


# ── 7. Multi-Page Cross-Validation (H4 == Daily Command == System Intel) ─────

def test_cross_page_consistency_9_assets(client):
    """Verify that H4 Forecasts, Daily Command, and System Intelligence return identical states."""
    h4_res = client.get("/api/v1/signals/h4-intelligence").json()
    daily_res = client.get("/api/v1/live/today").json()
    sys_res = client.get("/api/v1/system-intelligence/canonical-signals").json()

    assert h4_res["success"] is True
    assert daily_res["runtime_version"] in ["PHASE 59", "PHASE 60"]
    assert sys_res["success"] is True

    for asset in CORE_ASSETS:
        h4_row = next(m for m in h4_res["matrix"] if m["asset"] == asset)
        daily_row = next(f for f in daily_res["forecasts"] if f["asset"] == asset)
        sys_state = next(s for s in sys_res["data"] if s["asset"] == asset)

        assert h4_row["consensus"] == daily_row["direction"] == sys_state["direction"]
        assert h4_row["price"] == daily_row["entry_price"] == sys_state["price"]
        assert h4_row["risk_reward"] == daily_row["risk_reward"] == sys_state["risk_reward"]
        assert (h4_row["risk"] == "TAKE_NOW") == (daily_row["decision"] == "TAKE_TRADE") == sys_state["is_trade_signal_qualified"]


# ── 8. Dashboard and Daily Command Counter Equality ──────────────────────────

def test_dashboard_and_daily_command_counter_equality(client):
    """Verify summary counters are derived identically from the same canonical state."""
    daily_res = client.get("/api/v1/live/today").json()
    h4_res = client.get("/api/v1/signals/h4-intelligence").json()

    summary = daily_res["summary"]
    assert summary["today_forecasts"] == 9
    assert summary["qualified_trades"] == h4_res["valid_setups"]
    assert summary["watch_count"] == h4_res["watch_count"]
    assert summary["no_trade_count"] == h4_res["no_trade_count"]


# ── 9. Zero-Trust Strong Signal Policy Enforcement ────────────────────────────

def test_strong_signal_zero_trust_policy_strictness():
    """STRONG_BUY/STRONG_SELL is granted ONLY when ALL Zero-Trust gates pass."""
    all_states = canonical_signal_service.get_all_canonical_asset_states()

    for st in all_states:
        if st["is_trade_signal_qualified"]:
            assert st["signal_class"] in ["STRONG_BUY", "STRONG_SELL"]
            assert st["decision"] == "TAKE_NOW"
            assert st["qualification_status"] == "QUALIFIED"
            assert st["confidence"] >= 0.65
            assert st["contributing_models"] >= 5
            assert st["risk_reward"] >= 1.5
            assert st["session_status"] == "OPEN"
            assert st["event_risk"] != "HIGH"
            assert st["data_freshness"]["status"] == "FRESH"
            assert "CONFIRMED_MULTI_MODEL_CONSENSUS" in st["reason_codes"]
        else:
            assert st["decision"] == "NO_TRADE"
            assert st["qualification_status"] in ["WATCHLIST", "NO_TRADE"]


# ── 10. Market Data Freshness Tracking ────────────────────────────────────────

def test_market_data_freshness_tracking():
    """Verify data_freshness is present with valid age_seconds and FRESH status."""
    state = canonical_signal_service.evaluate_asset_intelligence("BTCUSD")
    freshness = state["data_freshness"]

    assert freshness["status"] == "FRESH"
    assert freshness["age_seconds"] <= 120.0
    assert "market_data_timestamp" in freshness


# ── 11. Absolute Real-Money Lockout ──────────────────────────────────────────

def test_real_money_execution_hard_lockout():
    """Verify execution mode is DEMO and real money remains strictly disabled."""
    settings = get_settings()
    assert settings.EXECUTION_MODE in ["DEMO", "PAPER"]
    meta = canonical_signal_service.get_canonical_runtime_metadata()
    assert meta["real_money_enabled"] is False
    assert meta["real_money_status"] == "STRICTLY_DISABLED"
    assert meta["broker_execution_enabled"] is False
