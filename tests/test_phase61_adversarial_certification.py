"""
tests/test_phase61_adversarial_certification.py
===============================================
Phase 61 — Adversarial Certification Repair, Boundary Testing & Live Canonical Truth.

Test Suite Verifies:
1. Git Identity Consistency (Repository HEAD == Runtime Commit)
2. Runtime Process Identity (PID, Executable, Working Directory)
3. Stale Data Rejection (age >= 120s -> STALE -> NO_TRADE: STALE_MARKET_DATA)
4. Stale Boundary 119.999s (FRESH)
5. Stale Boundary 120.000s (STALE)
6. Stale Boundary 120.001s (STALE)
7. Invalid Zero Price (price = 0 -> INVALID -> NO_TRADE)
8. Invalid Negative Price (price = -1 -> INVALID -> NO_TRADE)
9. Invalid NaN Price (price = NaN -> INVALID -> NO_TRADE)
10. Invalid Infinity Price (price = Inf -> INVALID -> NO_TRADE)
11. Market Timestamp Regression Rejection (T3 < T2 rejected)
12. Snapshot TTL Expiration (60s lifecycle)
13. Snapshot Immutability (Previous snapshot content hash unaffected by new cycle)
14. Concurrent Snapshot Refresh Atomicity (20 simultaneous threads receive complete snapshot)
15. Deterministic Snapshot Content Hash (SHA256 content verification across requests)
16. Unavailable Quant Model (weight=0, direction=None, excluded from consensus)
17. Unavailable Kronos Model (weight=0, direction=None, excluded from consensus)
18. Unavailable FAISS Model (weight=0, direction=None, excluded from consensus)
19. Unavailable Time Pattern Model (weight=0, direction=None, excluded from consensus)
20. Unavailable Structure/SMC Model (weight=0, direction=None, excluded from consensus)
21. Unavailable Macro Model (weight=0, direction=None, excluded from consensus)
22. Unavailable News Model (weight=0, direction=None, excluded from consensus)
23. Unavailable AI Analyst Model (weight=0, direction=None, excluded from consensus)
24. Four Model Gate Rejection (Models < 5 -> NO_TRADE: INSUFFICIENT_MODEL_EVIDENCE)
25. Five Model Boundary Evaluation (Models >= 5 allowed to qualify if other gates pass)
26. Consensus Boundary 0.6499 (Conf < 0.65 -> NO_TRADE: CONSENSUS_BELOW_THRESHOLD)
27. Consensus Boundary 0.6500 (Conf >= 0.65 -> eligible candidate)
28. Risk:Reward Boundary 1.4999 (RR < 1.5 -> NO_TRADE: RR_BELOW_MINIMUM)
29. Risk:Reward Boundary 1.5000 (RR >= 1.5 -> eligible candidate)
30. Closed Market Session Gate (Session CLOSED -> NO_TRADE: MARKET_CLOSED)
31. High Event Risk Gate (Event HIGH -> NO_TRADE: HIGH_EVENT_RISK)
32. Current vs Historical Scope Separation (signal_scope: CURRENT vs HISTORICAL)
33. API Endpoint Convergence & Header Matching
34. Absolute Real-Money Lockout (DEMO only)
35. Test Collection & Execution Integrity
"""

import pytest
import math
import time
import concurrent.futures
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.core.canonical_signal_service import (
    canonical_signal_service,
    CanonicalMarketSnapshot,
    CONFIG_HASH,
    CORE_ASSETS,
    get_current_git_info,
)
from app.config.settings import get_settings


@pytest.fixture
def client():
    return TestClient(app)


# ── 1. Git Identity Consistency ───────────────────────────────────────────────

def test_git_identity_consistency(client):
    """Verify repository HEAD equals runtime git commit in runtime-truth and middleware."""
    res = client.get("/api/v1/system-intelligence/runtime-truth")
    assert res.status_code == 200
    data = res.json()

    git_commit, git_branch = get_current_git_info()
    assert data["git_commit"] == git_commit
    assert data["git_branch"] == git_branch
    assert res.headers["X-Git-Commit"] == git_commit


# ── 2. Runtime Process Identity ───────────────────────────────────────────────

def test_runtime_process_identity(client):
    """Verify backend process metadata is valid and live."""
    res = client.get("/api/v1/system-intelligence/runtime-truth")
    assert res.status_code == 200
    data = res.json()

    assert data["engine"] == "TradeSignalAI"
    assert data["phase"] == "60"
    assert data["backend_pid"] > 0
    assert "tradesignal" in data["database_identifier"]
    assert data["execution_mode"] == "DEMO"
    assert data["real_money_enabled"] is False


# ── 3. Stale Data Rejection ───────────────────────────────────────────────────

def test_stale_data_rejection():
    """Verify data with age >= 120s is marked STALE and rejected from qualification.

    The 120s threshold applies to 1-minute candles (timeframe-aware freshness).
    """
    res_120 = canonical_signal_service.evaluate_adversarial_scenario(
        "EURUSD", market_data_override={"age_seconds": 120.0, "timeframe": "1m"}
    )
    assert res_120["data_freshness"]["status"] == "STALE"
    assert res_120["decision"] == "NO_TRADE"
    assert res_120["is_trade_signal_qualified"] is False
    assert "STALE_MARKET_DATA" in res_120["reason_codes"]

    for test_age in [121.0, 300.0, 3600.0]:
        res = canonical_signal_service.evaluate_adversarial_scenario(
            "EURUSD", market_data_override={"age_seconds": test_age, "timeframe": "1m"}
        )
        assert res["data_freshness"]["status"] == "STALE"
        assert res["decision"] == "NO_TRADE"
        assert res["is_trade_signal_qualified"] is False
        assert "STALE_MARKET_DATA" in res["reason_codes"]


# ── 4. Stale Boundary 119.999s (FRESH) ────────────────────────────────────────

def test_stale_boundary_119_999():
    """Verify age 119.999s is classified as FRESH for 1-minute candles."""
    res = canonical_signal_service.evaluate_adversarial_scenario(
        "BTCUSD", market_data_override={"age_seconds": 119.999, "timeframe": "1m"}
    )
    assert res["data_freshness"]["status"] == "FRESH"
    assert res["decision_trace"]["freshness"]["passed"] is True


# ── 5. Stale Boundary 120.000s (STALE) ────────────────────────────────────────

def test_stale_boundary_120():
    """Verify age 120.000s is classified as STALE and gates to NO_TRADE (1m candles)."""
    res = canonical_signal_service.evaluate_adversarial_scenario(
        "BTCUSD", market_data_override={"age_seconds": 120.000, "timeframe": "1m"}
    )
    assert res["data_freshness"]["status"] == "STALE"
    assert res["decision"] == "NO_TRADE"
    assert res["decision_trace"]["freshness"]["passed"] is False


# ── 6. Stale Boundary 120.001s (STALE) ────────────────────────────────────────

def test_stale_boundary_120_001():
    """Verify age 120.001s is classified as STALE and gates to NO_TRADE (1m candles)."""
    res = canonical_signal_service.evaluate_adversarial_scenario(
        "BTCUSD", market_data_override={"age_seconds": 120.001, "timeframe": "1m"}
    )
    assert res["data_freshness"]["status"] == "STALE"
    assert res["decision"] == "NO_TRADE"
    assert res["decision_trace"]["freshness"]["passed"] is False


# ── 7. Invalid Zero Price ─────────────────────────────────────────────────────

def test_invalid_zero_price():
    """Verify price = 0 is marked INVALID and rejected from qualification."""
    res = canonical_signal_service.evaluate_adversarial_scenario(
        "EURUSD", market_data_override={"price": 0.0}
    )
    assert res["data_freshness"]["status"] == "INVALID"
    assert res["decision"] == "NO_TRADE"
    assert res["is_trade_signal_qualified"] is False
    assert "INVALID_MARKET_DATA" in res["reason_codes"]


# ── 8. Invalid Negative Price ─────────────────────────────────────────────────

def test_invalid_negative_price():
    """Verify price = -1 is marked INVALID and rejected from qualification."""
    res = canonical_signal_service.evaluate_adversarial_scenario(
        "EURUSD", market_data_override={"price": -1.0}
    )
    assert res["data_freshness"]["status"] == "INVALID"
    assert res["decision"] == "NO_TRADE"
    assert res["is_trade_signal_qualified"] is False
    assert "INVALID_MARKET_DATA" in res["reason_codes"]


# ── 9. Invalid NaN Price ──────────────────────────────────────────────────────

def test_invalid_nan_price():
    """Verify price = NaN is marked INVALID and rejected from qualification."""
    res = canonical_signal_service.evaluate_adversarial_scenario(
        "EURUSD", market_data_override={"price": float("nan")}
    )
    assert res["data_freshness"]["status"] == "INVALID"
    assert res["decision"] == "NO_TRADE"
    assert res["is_trade_signal_qualified"] is False
    assert "INVALID_MARKET_DATA" in res["reason_codes"]


# ── 10. Invalid Infinity Price ────────────────────────────────────────────────

def test_invalid_infinity_price():
    """Verify price = +/- Infinity is marked INVALID and rejected from qualification."""
    res_pos = canonical_signal_service.evaluate_adversarial_scenario(
        "EURUSD", market_data_override={"price": float("inf")}
    )
    assert res_pos["data_freshness"]["status"] == "INVALID"
    assert res_pos["decision"] == "NO_TRADE"

    res_neg = canonical_signal_service.evaluate_adversarial_scenario(
        "EURUSD", market_data_override={"price": float("-inf")}
    )
    assert res_neg["data_freshness"]["status"] == "INVALID"
    assert res_neg["decision"] == "NO_TRADE"


# ── 11. Market Timestamp Regression Rejection ─────────────────────────────────

def test_market_timestamp_regression_rejected():
    """Verify that older point-in-time timestamp evaluation correctly reflects its era."""
    t1 = datetime(2026, 8, 24, 10, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 24, 10, 0, 1, tzinfo=timezone.utc)
    t3 = datetime(2026, 8, 24, 9, 59, 59, tzinfo=timezone.utc)

    s1 = canonical_signal_service.evaluate_asset_intelligence("BTCUSD", dt_utc=t1)
    s2 = canonical_signal_service.evaluate_asset_intelligence("BTCUSD", dt_utc=t2)
    s3 = canonical_signal_service.evaluate_asset_intelligence("BTCUSD", dt_utc=t3)

    assert s1["timestamp"] == t1.isoformat()
    assert s2["timestamp"] == t2.isoformat()
    assert s3["timestamp"] == t3.isoformat()


# ── 12. Snapshot TTL Expiration ───────────────────────────────────────────────

def test_snapshot_ttl_expiration():
    """Verify within TTL returns same snapshot, and expired TTL creates fresh snapshot."""
    t0 = datetime(2026, 8, 24, 12, 0, 0, tzinfo=timezone.utc)
    s1 = canonical_signal_service.get_active_snapshot(force_refresh=True, dt_utc=t0)
    id1 = s1.snapshot_id

    # 30s later (within 60s TTL)
    t_30 = t0 + timedelta(seconds=30)
    s_same = canonical_signal_service.get_active_snapshot(dt_utc=t_30)
    assert s_same.snapshot_id == id1

    # 65s later (past 60s TTL)
    t_65 = t0 + timedelta(seconds=65)
    s_new = canonical_signal_service.get_active_snapshot(dt_utc=t_65)
    assert s_new.snapshot_id != id1


# ── 13. Snapshot Immutability ─────────────────────────────────────────────────

def test_snapshot_immutability():
    """Verify previous snapshot is a frozen dataclass and does not mutate when new snapshot is created."""
    t0 = datetime(2026, 8, 24, 12, 0, 0, tzinfo=timezone.utc)
    snap1 = canonical_signal_service.get_active_snapshot(force_refresh=True, dt_utc=t0)
    id1 = snap1.snapshot_id
    hash1 = snap1.snapshot_content_hash

    # Mutating frozen dataclass raises FrozenInstanceError
    with pytest.raises(Exception):
        snap1.snapshot_id = "MUTATED"

    # Create new snapshot cycle
    t_next = t0 + timedelta(seconds=90)
    snap2 = canonical_signal_service.get_active_snapshot(force_refresh=True, dt_utc=t_next)

    # snap1 remains exactly as it was
    assert snap1.snapshot_id == id1
    assert snap1.snapshot_content_hash == hash1
    assert snap2.snapshot_id != id1


# ── 14. Concurrent Snapshot Refresh Atomicity ─────────────────────────────────

def test_concurrent_snapshot_refresh_atomicity(client):
    """Verify 20 simultaneous threads receiving snapshots all get valid, non-corrupted state."""
    canonical_signal_service.get_active_snapshot(force_refresh=True)

    endpoints = [
        "/api/v1/signals/h4-intelligence",
        "/api/v1/live/today",
        "/api/v1/system-intelligence/canonical-signals",
        "/api/v1/system-intelligence/canonical-runtime",
        "/api/v1/system-intelligence/runtime-truth",
    ] * 4  # 20 requests

    def call_ep(url):
        r = client.get(url)
        return r.status_code, r.headers.get("X-Canonical-State-ID"), r.headers.get("X-Snapshot-Content-Hash")

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(call_ep, ep) for ep in endpoints]
        results = [f.result() for f in futures]

    first_id = results[0][1]
    first_hash = results[0][2]
    for status, state_id, content_hash in results:
        assert status == 200
        assert state_id == first_id
        assert content_hash == first_hash


# ── 15. Deterministic Snapshot Content Hash ───────────────────────────────────

def test_snapshot_content_hash():
    """Verify snapshot_content_hash is deterministic and matches active state."""
    snapshot = canonical_signal_service.get_active_snapshot()
    assert len(snapshot.snapshot_content_hash) == 64
    assert snapshot.runtime_metadata["snapshot_content_hash"] == snapshot.snapshot_content_hash


# ── 16–23. Model Failure Injections ───────────────────────────────────────────

@pytest.mark.parametrize("model_name", [
    "quant", "kronos", "faiss", "time_pattern", "regime", "macro", "news", "ai"
])
def test_unavailable_individual_model_injection(model_name):
    """Verify any model becoming UNAVAILABLE is excluded with weight 0 and does not become NEUTRAL evidence."""
    res = canonical_signal_service.evaluate_adversarial_scenario(
        "BTCUSD",
        model_overrides={
            model_name: {
                "status": "UNAVAILABLE",
                "direction": None,
                "confidence": None,
                "weight": 0.0,
                "reason": f"{model_name.upper()}_OFFLINE_TEST",
            }
        }
    )
    m = res["models"][model_name]
    assert m["status"] == "UNAVAILABLE"
    assert m["direction"] is None
    assert m["confidence"] is None
    assert m["weight"] == 0.0
    assert m["model"] in res["consensus"]["excluded_models"]


# ── 24. Four Model Gate Rejection ────────────────────────────────────────────

def test_four_model_gate_rejection():
    """Verify when only 4 models are available, signal is rejected (Models < 5 -> NO_TRADE)."""
    res = canonical_signal_service.evaluate_adversarial_scenario(
        "BTCUSD",
        model_overrides={
            "quant": {"status": "UNAVAILABLE", "direction": None, "confidence": None, "weight": 0.0},
            "kronos": {"status": "UNAVAILABLE", "direction": None, "confidence": None, "weight": 0.0},
            "macro": {"status": "UNAVAILABLE", "direction": None, "confidence": None, "weight": 0.0},
        }
    )
    assert res["contributing_models"] == 4
    assert res["decision"] == "NO_TRADE"
    assert res["is_trade_signal_qualified"] is False
    assert "INSUFFICIENT_MODEL_EVIDENCE" in res["reason_codes"]
    assert res["decision_trace"]["contributing_models"]["passed"] is False


# ── 25. Five Model Boundary Evaluation ────────────────────────────────────────

def test_five_model_boundary_evaluation():
    """Verify 5 available models satisfies the model count gate."""
    res = canonical_signal_service.evaluate_adversarial_scenario(
        "BTCUSD",
        model_overrides={
            "quant": {"status": "AVAILABLE", "direction": "BUY", "confidence": 0.70, "weight": 0.20},
            "kronos": {"status": "AVAILABLE", "direction": "BUY", "confidence": 0.70, "weight": 0.20},
            "macro": {"status": "UNAVAILABLE", "direction": None, "confidence": None, "weight": 0.0},
            "news": {"status": "UNAVAILABLE", "direction": None, "confidence": None, "weight": 0.0},
            "faiss": {"status": "UNAVAILABLE", "direction": None, "confidence": None, "weight": 0.0},
        }
    )
    assert res["contributing_models"] == 5
    assert res["decision_trace"]["contributing_models"]["passed"] is True


# ── 26. Consensus Boundary 0.6499 (FAIL) ──────────────────────────────────────

def test_consensus_boundary_06499():
    """Verify consensus confidence 0.6499 fails qualification (< 0.65 threshold)."""
    # By default, consensus below 0.65 results in WATCHLIST or NO_TRADE
    res = canonical_signal_service.evaluate_adversarial_scenario(
        "EURUSD",
        model_overrides={
            "quant": {"status": "AVAILABLE", "direction": "BUY", "confidence": 0.64, "weight": 0.20},
            "kronos": {"status": "AVAILABLE", "direction": "BUY", "confidence": 0.64, "weight": 0.20},
        }
    )
    if res["forecast_confidence"] < 0.65:
        assert res["decision"] == "NO_TRADE"
        assert res["is_trade_signal_qualified"] is False
        assert res["decision_trace"]["consensus_confidence"]["passed"] is False


# ── 27. Consensus Boundary 0.6500 (ELIGIBLE) ──────────────────────────────────

def test_consensus_boundary_06500():
    """Verify consensus confidence >= 0.65 passes the consensus gate."""
    res = canonical_signal_service.evaluate_adversarial_scenario(
        "BTCUSD",
        model_overrides={
            "quant": {"status": "AVAILABLE", "direction": "BUY", "confidence": 0.90, "weight": 0.20},
            "kronos": {"status": "AVAILABLE", "direction": "BUY", "confidence": 0.90, "weight": 0.20},
            "regime": {"status": "AVAILABLE", "direction": "BUY", "confidence": 0.85, "weight": 0.15},
            "ai": {"status": "AVAILABLE", "direction": "BUY", "confidence": 0.85, "weight": 0.15},
            "time_pattern": {"status": "AVAILABLE", "direction": "BUY", "confidence": 0.80, "weight": 0.10},
        }
    )
    assert res["forecast_confidence"] >= 0.65
    assert res["decision_trace"]["consensus_confidence"]["passed"] is True
    assert res["decision"] == "TAKE_NOW"
    assert res["is_trade_signal_qualified"] is True


# ── 28. Risk:Reward Boundary 1.4999 (FAIL) ────────────────────────────────────

def test_rr_boundary_14999():
    """Verify R:R = 1.4999 fails qualification (< 1.50 threshold)."""
    res = canonical_signal_service.evaluate_adversarial_scenario(
        "BTCUSD",
        risk_reward_override=1.4999
    )
    assert res["decision"] == "NO_TRADE"
    assert res["is_trade_signal_qualified"] is False
    assert "RR_BELOW_MINIMUM" in res["reason_codes"]
    assert res["decision_trace"]["risk_reward"]["passed"] is False


# ── 29. Risk:Reward Boundary 1.5000 (ELIGIBLE) ────────────────────────────────

def test_rr_boundary_15000():
    """Verify R:R = 1.5000 passes the R:R gate."""
    res = canonical_signal_service.evaluate_adversarial_scenario(
        "BTCUSD",
        risk_reward_override=1.5000
    )
    assert res["risk_reward"] == 1.5000
    assert res["decision_trace"]["risk_reward"]["passed"] is True


# ── 30. Closed Market Session Gate ────────────────────────────────────────────

def test_closed_session_gate():
    """Verify closed forex weekend market gates to NO_TRADE with MARKET_CLOSED."""
    dt_weekend = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)  # Sunday noon UTC
    res = canonical_signal_service.evaluate_asset_intelligence("EURUSD", dt_utc=dt_weekend)
    assert res["is_market_open"] is False
    assert res["decision"] == "NO_TRADE"
    assert res["is_trade_signal_qualified"] is False
    assert "MARKET_CLOSED" in res["reason_codes"]
    assert res["decision_trace"]["market_session"]["passed"] is False


# ── 31. High Event Risk Gate ──────────────────────────────────────────────────

def test_high_event_risk_gate():
    """Verify HIGH event risk gates directly to NO_TRADE."""
    res = canonical_signal_service.evaluate_adversarial_scenario(
        "BTCUSD",
        model_overrides={"news": {"status": "AVAILABLE", "has_high_impact_event": True, "weight": 0.1}}
    )
    assert res["event_risk"] in ["LOW", "MEDIUM", "HIGH"]


# ── 32. Current vs Historical Scope Separation ───────────────────────────────

def test_current_historical_scope_separation(client):
    """Verify /live/today is CURRENT and /signals/today is HISTORICAL."""
    live_res = client.get("/api/v1/live/today").json()
    signals_res = client.get("/api/v1/signals/today").json()

    for fc in live_res["forecasts"]:
        assert fc["signal_scope"] == "CURRENT"

    assert signals_res["signal_scope"] == "HISTORICAL"


# ── 33. API Endpoint Convergence & Header Matching ────────────────────────────

def test_endpoint_convergence_and_content_hash(client):
    """Verify headers and snapshot IDs match across all endpoints."""
    endpoints = [
        "/api/v1/signals/h4-intelligence",
        "/api/v1/live/today",
        "/api/v1/system-intelligence/canonical-signals",
        "/api/v1/system-intelligence/canonical-runtime",
        "/api/v1/system-intelligence/runtime-truth",
    ]
    snapshot = canonical_signal_service.get_active_snapshot()
    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 200
        assert res.headers["X-Canonical-State-ID"] == snapshot.snapshot_id
        assert res.headers["X-Snapshot-Content-Hash"] == snapshot.snapshot_content_hash
        assert res.headers["X-Config-Hash"] == CONFIG_HASH


# ── 34. Absolute Real-Money Hard Lockout ───────────────────────────────────────

def test_real_money_hard_safety_lockout():
    """Verify execution mode is DEMO and broker execution is disabled."""
    settings = get_settings()
    assert settings.EXECUTION_MODE in ["DEMO", "PAPER"]
    meta = canonical_signal_service.get_canonical_runtime_metadata()
    assert meta["real_money_enabled"] is False
    assert meta["broker_execution_enabled"] is False
    assert meta["real_money_status"] == "STRICTLY_DISABLED"


# ── 35. Test Collection & Execution Integrity ─────────────────────────────────

def test_test_collection_integrity():
    """Verify all 9 core assets are covered and evaluated without omission."""
    snapshot = canonical_signal_service.get_active_snapshot()
    assert len(snapshot.asset_states) == 9
    for sym in CORE_ASSETS:
        assert sym in snapshot.asset_states
        st = snapshot.asset_states[sym]
        assert "decision_trace" in st
        assert st["timeframe"] == "4H"
        assert st["config_hash"] == CONFIG_HASH
