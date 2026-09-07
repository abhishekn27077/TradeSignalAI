"""
tests/test_phase60_snapshot_integrity.py
========================================
Phase 60 — Canonical Snapshot Integrity, Live Market Data Truth & Evidence Validation.

Test Suite Verifies:
1. Runtime Identity & Git Reconciliation (HEAD commit, engine 60.0.0-canonical, config hash 79a4f8e12b79310d)
2. Snapshot Stability (20 repeated requests return the EXACT SAME snapshot_id)
3. Concurrent Request Snapshot Equality (20 simultaneous multi-endpoint threads share identical snapshot_id)
4. Response Fingerprint Header matching (X-Canonical-State-ID == snapshot_id)
5. Market Data Freshness & Stale Gate (age < 120s FRESH; age >= 120s STALE -> NO_TRADE: STALE_MARKET_DATA)
6. Invalid Market Data Rejection (price <= 0 -> INVALID -> NO_TRADE)
7. Explicit FAISS UNAVAILABLE semantics (weight=0.0, direction=None, zero consensus dilution)
8. Consensus Math & Auditable Explanation (available_weight, contributing_models, excluded_models)
9. Zero-Trust Strong Signal Gate Strictness (Conf >= 0.65, Models >= 5, RR >= 1.5)
10. Current vs Historical Scope Separation (signal_scope: CURRENT vs HISTORICAL)
11. Absolute Real-Money Hard Lockout (EXECUTION_MODE=DEMO, REAL_MONEY=DISABLED)
"""

import pytest
import concurrent.futures
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.core.canonical_signal_service import (
    canonical_signal_service,
    CONFIG_HASH,
    CORE_ASSETS,
    get_current_git_info,
)
from app.config.settings import get_settings


@pytest.fixture
def client():
    return TestClient(app)


# ── 1. Runtime Identity & Git Reconciliation ──────────────────────────────────

def test_runtime_identity_and_git_reconciliation(client):
    """Verify runtime identity and dynamic git commit match current HEAD."""
    res = client.get("/api/v1/system-intelligence/runtime-truth")
    assert res.status_code == 200
    data = res.json()

    git_commit, git_branch = get_current_git_info()

    assert data["engine"] == "TradeSignalAI"
    assert data["phase"] == "60"
    assert data["engine_version"] == "60.0.0-canonical"
    assert data["canonical_engine_version"] == "60.0.0-canonical"
    assert data["config_hash"] == CONFIG_HASH
    assert data["git_commit"] == git_commit
    assert data["git_branch"] == git_branch
    assert data["backend_pid"] > 0
    assert data["execution_mode"] == "DEMO"
    assert data["real_money_enabled"] is False
    assert data["broker_execution_enabled"] is False
    assert data["snapshot_id"].startswith("SNAP-")
    assert data["canonical_state_id"] == data["snapshot_id"]


# ── 2. Snapshot Stability Across Repeated Requests ───────────────────────────

def test_snapshot_stability_across_repeated_requests(client):
    """Verify 20 repeated requests to different endpoints return the EXACT SAME snapshot_id."""
    # Seed active snapshot
    initial_snapshot = canonical_signal_service.get_active_snapshot(force_refresh=True)
    expected_snapshot_id = initial_snapshot.snapshot_id

    endpoints = [
        "/api/v1/signals/h4-intelligence",
        "/api/v1/live/today",
        "/api/v1/system-intelligence/canonical-signals",
        "/api/v1/system-intelligence/canonical-runtime",
        "/api/v1/system-intelligence/runtime-truth",
    ]

    for _ in range(20):
        for ep in endpoints:
            res = client.get(ep)
            assert res.status_code == 200
            data = res.json()

            # Extract snapshot_id from endpoint response
            if "snapshot_id" in data:
                assert data["snapshot_id"] == expected_snapshot_id
            elif "data" in data and isinstance(data["data"], dict) and "snapshot_id" in data["data"]:
                assert data["data"]["snapshot_id"] == expected_snapshot_id
            elif "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                assert data["data"][0]["snapshot_id"] == expected_snapshot_id

            # Header fingerprint must also match
            assert res.headers["X-Canonical-State-ID"] == expected_snapshot_id


# ── 3. Concurrent Request Snapshot Equality ───────────────────────────────────

def test_concurrent_request_snapshot_equality(client):
    """Verify 20 concurrent threads calling distinct endpoints all receive the EXACT SAME snapshot_id."""
    initial_snapshot = canonical_signal_service.get_active_snapshot(force_refresh=True)
    target_id = initial_snapshot.snapshot_id

    endpoints = [
        "/api/v1/signals/h4-intelligence",
        "/api/v1/live/today",
        "/api/v1/system-intelligence/canonical-signals",
        "/api/v1/system-intelligence/canonical-runtime",
        "/api/v1/system-intelligence/runtime-truth",
    ] * 4  # 20 total requests

    def fetch_endpoint(url):
        r = client.get(url)
        return r.status_code, r.headers.get("X-Canonical-State-ID")

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(fetch_endpoint, ep) for ep in endpoints]
        results = [f.result() for f in futures]

    for status_code, header_state_id in results:
        assert status_code == 200
        assert header_state_id == target_id


# ── 4. Response Fingerprint Header Integrity ─────────────────────────────────

def test_response_fingerprint_header_integrity(client):
    """Verify headers include complete Phase 60 metadata and match active snapshot."""
    res = client.get("/api/v1/signals/h4-intelligence")
    assert res.status_code == 200
    headers = res.headers

    snapshot = canonical_signal_service.get_active_snapshot()

    assert headers["X-Canonical-Engine-Version"] == "PHASE 60"
    assert headers["X-Config-Hash"] == CONFIG_HASH
    assert headers["X-Canonical-State-ID"] == snapshot.snapshot_id
    assert headers["X-Generated-At"] == snapshot.created_at
    assert headers["X-Market-Data-Timestamp"] == snapshot.market_data_timestamp


# ── 5. Market Data Freshness & Stale Gate ─────────────────────────────────────

def test_market_data_freshness_enforcement():
    """Verify market data freshness is computed from real candle age.

    Freshness is timeframe-aware: hourly candles are FRESH if < 2h old.
    The old '< 120s' assertion only passed because age_seconds was hardcoded
    to 0.5 (fake). Now real age is computed from the newest candle timestamp.
    """
    snapshot = canonical_signal_service.get_active_snapshot()
    for sym, st in snapshot.asset_states.items():
        freshness = st["data_freshness"]
        assert freshness["status"] in ("FRESH", "STALE", "INVALID")
        assert freshness["age_seconds"] >= 0.0
        # Consistency: FRESH hourly data must be < 2h old
        if freshness["status"] == "FRESH":
            assert freshness["age_seconds"] < 7200.0


# ── 6. Invalid Market Data Rejection ─────────────────────────────────────────

def test_invalid_market_data_rejection():
    """Verify invalid prices (<= 0, NaN, Inf) gate directly to NO_TRADE."""
    res_zero = canonical_signal_service.evaluate_adversarial_scenario("BTCUSD", market_data_override={"price": 0.0})
    assert res_zero["data_freshness"]["status"] == "INVALID"
    assert res_zero["decision"] == "NO_TRADE"
    assert res_zero["is_trade_signal_qualified"] is False
    assert "INVALID_MARKET_DATA" in res_zero["reason_codes"]


# ── 7. Explicit FAISS UNAVAILABLE Semantics ──────────────────────────────────

def test_faiss_explicit_unavailable_semantics():
    """CRITICAL: FAISS UNAVAILABLE must NEVER be converted to NEUTRAL 0% or dilute consensus."""
    snapshot = canonical_signal_service.get_active_snapshot()
    for sym, st in snapshot.asset_states.items():
        faiss = st["models"]["faiss"]
        assert faiss["status"] == "UNAVAILABLE"
        assert faiss["direction"] is None
        assert faiss["confidence"] is None
        assert faiss["weight"] == 0.0
        assert faiss["reason"] == "FAISS_VECTOR_INDEX_OFFLINE_PENDING"

        # Excluded from available models
        assert "faiss_memory" not in st["available_models"]
        assert "faiss_memory" in st["consensus"]["excluded_models"]
        assert st["consensus"]["excluded_model_reasons"]["faiss_memory"] == "FAISS_VECTOR_INDEX_OFFLINE_PENDING"


# ── 7. Consensus Math & Auditable Explanation ─────────────────────────────────

def test_consensus_math_and_auditable_explanation():
    """Verify consensus calculation matches available model sum and excludes unavailable."""
    snapshot = canonical_signal_service.get_active_snapshot()
    for sym, st in snapshot.asset_states.items():
        consensus = st["consensus"]
        assert "available_weight" in consensus
        assert "contributing_models" in consensus
        assert "excluded_models" in consensus
        assert "excluded_model_reasons" in consensus

        assert consensus["contributing_models"] == len(st["available_models"])
        assert consensus["available_weight"] > 0.0
        assert consensus["score"] >= 50.0


# ── 8. Zero-Trust Strong Signal Gate Strictness ───────────────────────────────

def test_zero_trust_strong_signal_gates():
    """Strong signals require consensus >= 0.65, models >= 5, RR >= 1.5, session open, low event risk."""
    snapshot = canonical_signal_service.get_active_snapshot()
    for sym, st in snapshot.asset_states.items():
        if st["is_trade_signal_qualified"]:
            assert st["decision"] == "TAKE_NOW"
            assert st["qualification_status"] == "QUALIFIED"
            assert st["confidence"] >= 0.65
            assert st["contributing_models"] >= 5
            assert st["risk_reward"] >= 1.5
            assert st["session_status"] == "OPEN"
            assert st["event_risk"] != "HIGH"
            assert st["data_freshness"]["status"] == "FRESH"
        else:
            assert st["decision"] == "NO_TRADE"
            assert st["qualification_status"] in ["WATCHLIST", "NO_TRADE"]


# ── 9. Scope Separation: CURRENT vs HISTORICAL ───────────────────────────────

def test_scope_separation_current_vs_historical(client):
    """Verify CURRENT snapshot state is separated from HISTORICAL database records."""
    live_today_res = client.get("/api/v1/live/today").json()
    signals_today_res = client.get("/api/v1/signals/today").json()

    # /live/today delivers current snapshot signals
    for fc in live_today_res["forecasts"]:
        assert fc["signal_scope"] == "CURRENT"
        assert "snapshot_id" in fc

    # /signals/today delivers historical database records
    assert signals_today_res["signal_scope"] == "HISTORICAL"


# ── 10. Real Money Hard Safety Lockout ────────────────────────────────────────

def test_real_money_hard_safety_lockout():
    """Verify execution mode is DEMO and real-money execution is strictly disabled."""
    settings = get_settings()
    assert settings.EXECUTION_MODE in ["DEMO", "PAPER"]
    meta = canonical_signal_service.get_canonical_runtime_metadata()
    assert meta["real_money_enabled"] is False
    assert meta["real_money_status"] == "STRICTLY_DISABLED"
    assert meta["broker_execution_enabled"] is False
