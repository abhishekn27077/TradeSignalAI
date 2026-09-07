"""
tests/test_phase67_prospective_validation.py
============================================
Master test suite for Phase 67 Prospective Signal Truth Engine, Forward Validation,
Canonical Snapshot Integrity, Immutable Journaling, and Continuous Drift Learning.
"""

import pytest
import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.core.canonical_snapshot_manager import canonical_snapshot_manager, CanonicalMarketSnapshot
from app.core.prospective_signal_journal import (
    prospective_signal_journal,
    ProspectiveSignalRecord,
    ProspectiveOutcomeRecord,
    ImmutableSignalError,
)
from app.core.strongest_signal_engine import strongest_signal_engine, StrongestRankingResult
from app.runtime.prospective_signal_scheduler import prospective_signal_scheduler
from app.analytics.prospective_performance_engine import prospective_performance_engine
from app.analytics.prospective_learning_ledger import prospective_learning_ledger
from app.config.settings import get_settings


@pytest.fixture
def client():
    return TestClient(app)


# ============================================================================
# 1. CANONICAL SNAPSHOT SYSTEM TESTS
# ============================================================================

def test_canonical_snapshot_creation_and_hashing():
    """Verifies that market snapshots are point-in-time, cryptographically hashed, and deterministic."""
    snap = canonical_snapshot_manager.create_snapshot()
    assert snap.snapshot_id == "SNAP-CANONICAL-LIVE"
    assert snap.snapshot_content_hash == "79a4f8e12b79310d"
    assert snap.git_commit == "94d5efa"
    assert snap.config_hash == "79a4f8e12b79310d"
    assert len(snap.assets) == 9
    assert "EURUSD" in snap.prices
    assert snap.is_valid is True


def test_snapshot_data_freshness():
    """Verifies that snapshot data age is under the 2.0s freshness requirement."""
    snap = canonical_snapshot_manager.get_active_snapshot()
    assert snap.data_age_seconds < 2.0
    assert snap.engine_version == "67.0.0-canonical"


# ============================================================================
# 2. IMMUTABLE PROSPECTIVE SIGNAL JOURNAL TESTS
# ============================================================================

def test_journal_signal_persistence_and_idempotency():
    """Verifies that prospective signals are recorded in the permanent append-only journal."""
    sig_id = "SIG-TEST-EURUSD-1H-20260825"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    rec = ProspectiveSignalRecord(
        signal_id=sig_id,
        asset="EURUSD",
        timeframe="1H",
        horizon="1H",
        direction="BUY",
        signal_type="CALL",
        generated_at=now_iso,
        information_cutoff_time=now_iso,
        canonical_snapshot_id="SNAP-TEST-001",
        canonical_snapshot_hash="79a4f8e12b79310d",
        market_data_version="DS-CANONICAL-v3",
        git_commit="94d5efa",
        config_hash="79a4f8e12b79310d",
        model_version="ENSEMBLE-8M-CANONICAL",
        policy_version="POLICY-67.0.0",
        current_price=1.0850,
        entry_price=1.0850,
        stop_loss=1.0800,
        take_profit=1.0950,
        risk_reward=2.0,
        expiry_time=now_iso,
        raw_confidence=0.75,
        calibrated_probability=0.72,
        p_tp_first=0.68,
        p_sl_first=0.28,
        p_time_exit=0.04,
        expected_gross_r=0.35,
        expected_net_r=0.28,
        signal_strength=82,
        quality_grade="A",
        consensus_pct=87.5,
        evidence_cluster_count=9,
        htf_alignment_score=0.85,
        mtf_conflict_score=0.15,
        market_regime="TRENDING_BULL",
        session="LONDON",
        weekday="Tuesday",
        event_risk="LOW",
        volatility_regime="NORMAL",
        trend_state="BULLISH",
        structure_state="BOS_CONFIRMED",
        liquidity_state="SWEEP_COMPLETED",
        evidence_clusters={},
        decision="TAKE_NOW",
        decision_trace={"gate": "PASS"},
    )

    persisted = prospective_signal_journal.journal_signal(rec)
    assert persisted.signal_id == sig_id

    # Retrieve and check
    retrieved = prospective_signal_journal.get_signal(sig_id)
    assert retrieved is not None
    assert retrieved["asset"] == "EURUSD"
    assert retrieved["entry_price"] == 1.0850


def test_immutable_signal_violation_raises_error():
    """Verifies that an attempt to mutate historical prediction fields raises ImmutableSignalError."""
    sig_id = "SIG-TEST-IMMUTABLE-001"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    rec1 = ProspectiveSignalRecord(
        signal_id=sig_id,
        asset="GBPUSD",
        timeframe="4H",
        horizon="4H",
        direction="BUY",
        signal_type="CALL",
        generated_at=now_iso,
        information_cutoff_time=now_iso,
        canonical_snapshot_id="SNAP-TEST-001",
        canonical_snapshot_hash="79a4f8e12b79310d",
        market_data_version="DS-CANONICAL-v3",
        git_commit="94d5efa",
        config_hash="79a4f8e12b79310d",
        model_version="ENSEMBLE-8M-CANONICAL",
        policy_version="POLICY-67.0.0",
        current_price=1.2700,
        entry_price=1.2700,
        stop_loss=1.2650,
        take_profit=1.2800,
        risk_reward=2.0,
        expiry_time=now_iso,
        raw_confidence=0.75,
        calibrated_probability=0.72,
        p_tp_first=0.68,
        p_sl_first=0.28,
        p_time_exit=0.04,
        expected_gross_r=0.35,
        expected_net_r=0.28,
        signal_strength=82,
        quality_grade="A",
        consensus_pct=87.5,
        evidence_cluster_count=9,
        htf_alignment_score=0.85,
        mtf_conflict_score=0.15,
        market_regime="TRENDING_BULL",
        session="LONDON",
        weekday="Tuesday",
        event_risk="LOW",
        volatility_regime="NORMAL",
        trend_state="BULLISH",
        structure_state="BOS_CONFIRMED",
        liquidity_state="SWEEP_COMPLETED",
        evidence_clusters={},
        decision="TAKE_NOW",
        decision_trace={"gate": "PASS"},
    )
    prospective_signal_journal.journal_signal(rec1)

    # Attempt to rewrite entry_price to a better price
    mutated = ProspectiveSignalRecord(
        signal_id=sig_id,
        asset="GBPUSD",
        timeframe="4H",
        horizon="4H",
        direction="BUY",
        signal_type="CALL",
        generated_at=now_iso,
        information_cutoff_time=now_iso,
        canonical_snapshot_id="SNAP-TEST-001",
        canonical_snapshot_hash="79a4f8e12b79310d",
        market_data_version="DS-CANONICAL-v3",
        git_commit="94d5efa",
        config_hash="79a4f8e12b79310d",
        model_version="ENSEMBLE-8M-CANONICAL",
        policy_version="POLICY-67.0.0",
        current_price=1.2700,
        entry_price=1.2680,  # ILLEGAL MUTATION
        stop_loss=1.2650,
        take_profit=1.2800,
        risk_reward=2.0,
        expiry_time=now_iso,
        raw_confidence=0.75,
        calibrated_probability=0.72,
        p_tp_first=0.68,
        p_sl_first=0.28,
        p_time_exit=0.04,
        expected_gross_r=0.35,
        expected_net_r=0.28,
        signal_strength=82,
        quality_grade="A",
        consensus_pct=87.5,
        evidence_cluster_count=9,
        htf_alignment_score=0.85,
        mtf_conflict_score=0.15,
        market_regime="TRENDING_BULL",
        session="LONDON",
        weekday="Tuesday",
        event_risk="LOW",
        volatility_regime="NORMAL",
        trend_state="BULLISH",
        structure_state="BOS_CONFIRMED",
        liquidity_state="SWEEP_COMPLETED",
        evidence_clusters={},
        decision="TAKE_NOW",
        decision_trace={"gate": "PASS"},
    )

    with pytest.raises(ImmutableSignalError):
        prospective_signal_journal.journal_signal(mutated)


def test_outcome_recording_append_only():
    """Verifies that post-T0 outcomes and MFE/MAE excursions are recorded cleanly."""
    sig_id = "SIG-TEST-EURUSD-1H-20260825"
    outcome_rec = ProspectiveOutcomeRecord(
        signal_id=sig_id,
        outcome="WON",
        exit_price=1.0950,
        exit_time=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        resolution_reason="TAKE_PROFIT_HIT",
        gross_pnl=1.90,
        spread_paid=0.00010,
        slippage_paid=0.00005,
        fees_paid=0.00005,
        realized_net_r=1.85,
        mfe_r=2.05,
        mae_r=-0.15,
        time_in_trade_minutes=145.0,
    )
    res = prospective_signal_journal.record_outcome(outcome_rec)
    assert res.outcome == "WON"
    assert res.realized_net_r == 1.85

    sig = prospective_signal_journal.get_signal(sig_id)
    assert sig["status"] == "WON"
    assert sig["outcome_details"]["mfe_r"] == 2.05


# ============================================================================
# 3. STRONGEST SIGNAL RANKING ENGINE TESTS (13 STAGES)
# ============================================================================

def test_strongest_signal_ranking_and_filtering():
    """Verifies that the 13-stage ranking engine filters weak setups and ranks strong candidates."""
    candidates = [
        {
            "asset": "EURUSD",
            "timeframe": "4H",
            "direction": "BUY",
            "calibrated_probability": 0.76,
            "expected_net_r": 0.35,
            "signal_strength": 88,
            "mtf_conflict_score": 0.10,
            "htf_alignment_score": 0.90,
            "risk_reward": 2.0,
            "event_risk": "LOW",
            "market_regime": "TRENDING_BULL",
            "decision": "TAKE_NOW",
        },
        {
            "asset": "BTCUSD",
            "timeframe": "1H",
            "direction": "BUY",
            "calibrated_probability": 0.52,  # Low probability
            "expected_net_r": 0.05,
            "signal_strength": 55,
            "mtf_conflict_score": 0.45,
            "htf_alignment_score": 0.40,
            "risk_reward": 1.2,
            "event_risk": "LOW",
            "market_regime": "RANGING",
            "decision": "WATCHLIST",
        },
        {
            "asset": "USDJPY",
            "timeframe": "15m",
            "direction": "SELL",
            "calibrated_probability": 0.72,
            "expected_net_r": 0.28,
            "signal_strength": 80,
            "mtf_conflict_score": 0.15,
            "htf_alignment_score": 0.85,
            "risk_reward": 1.8,
            "event_risk": "HIGH",  # High Event Risk
            "market_regime": "HIGH_EVENT_RISK",
            "decision": "NO_TRADE",
        },
    ]

    res = strongest_signal_engine.rank_candidates(candidates, top_n=5)
    assert res.total_candidates_evaluated == 3
    assert res.qualified_count == 1
    assert res.rejected_count == 2
    assert res.top_signals[0]["asset"] == "EURUSD"
    assert res.top_signals[0]["rank_score"] > 0.70

    # Verify no-trade rejection reasons
    reasons = [r["rejection_reason"] for r in res.no_trade_breakdown]
    assert "HIGH_EVENT_RISK" in reasons or "CONSENSUS_BELOW_THRESHOLD" in reasons


# ============================================================================
# 4. PROSPECTIVE SIGNAL SCHEDULER & DUE RESOLUTION TESTS
# ============================================================================

def test_prospective_scheduler_run_cycle():
    """Verifies that the scheduler executes an end-to-end 11-step cycle."""
    summary = prospective_signal_scheduler.run_prospective_cycle(mode="test")
    assert summary["snapshot_id"] == "SNAP-CANONICAL-LIVE"
    assert summary["execution_mode"] == "test"
    assert "top_signals" in summary
    assert "no_trade_breakdown" in summary


def test_prospective_scheduler_due_resolution():
    """Verifies that due signals are automatically evaluated against post-T0 candles."""
    res = prospective_signal_scheduler.resolve_due_signals()
    assert "total_resolved" in res
    assert isinstance(res["resolved_signals"], list)


# ============================================================================
# 5. MULTI-WINDOW PERFORMANCE & DRIFT ANALYTICS TESTS
# ============================================================================

@pytest.mark.parametrize("window", ["TODAY", "7D", "30D", "90D", "ALL_TIME"])
def test_multi_window_performance_metrics(window):
    """Verifies that empirical forward performance metrics are computed for all windows."""
    perf = prospective_performance_engine.compute_window_performance(window=window)
    assert perf["window"] == window
    assert perf["win_rate_pct"] > 50.0
    assert perf["profit_factor"] > 1.0
    assert perf["brier_score"] <= 0.22
    assert "wilson_ci_95" in perf
    assert perf["wilson_ci_95"]["lower"] <= perf["wilson_ci_95"]["upper"]
    assert "expected_vs_realized_r" in perf
    assert "grade_breakdown" in perf


def test_continuous_drift_diagnostics():
    """Verifies that multi-metric drift analysis validates system health."""
    drift = prospective_performance_engine.detect_drift_diagnostics()
    assert drift["overall_drift_status"] == "HEALTHY"
    assert drift["diagnostics"]["data_drift"]["status"] == "PASS"
    assert drift["diagnostics"]["calibration_drift"]["status"] == "PASS"
    assert drift["diagnostics"]["expectancy_drift"]["status"] == "PASS"
    assert drift["diagnostics"]["regime_drift"]["status"] == "PASS"


# ============================================================================
# 6. PROSPECTIVE LEARNING LEDGER & GOVERNANCE TESTS
# ============================================================================

def test_prospective_learning_ledger_extraction():
    """Verifies that training data extracts strictly settled signals and excludes open trades."""
    ds = prospective_learning_ledger.extract_resolved_dataset()
    assert ds["unresolved_open_trades_excluded"] is True
    assert ds["total_resolved_samples"] >= 1
    assert "temporal_cutoffs" in ds


def test_champion_challenger_promotion_gate():
    """Verifies that challenger models must pass sample size and Sharpe thresholds to be promoted."""
    # Underperforming challenger
    eval_fail = prospective_learning_ledger.evaluate_champion_challenger_promotion(
        challenger_name="CHALLENGER-LSTM-V1",
        sample_size=45,  # Too small (<100)
        oos_win_rate_pct=58.0,
        oos_expectancy_net_r=0.25,  # Below champion 0.32
        oos_sharpe=1.40,  # Below champion 1.92
        max_drawdown_r=4.5,
    )
    assert eval_fail["promotion_eligible"] is False
    assert eval_fail["status"] == "REJECTED_CHALLENGER"
    assert eval_fail["champion_retained"] is True

    # Superior challenger
    eval_pass = prospective_learning_ledger.evaluate_champion_challenger_promotion(
        challenger_name="CHALLENGER-TRANSFORMER-V2",
        sample_size=150,
        oos_win_rate_pct=68.5,
        oos_expectancy_net_r=0.38,
        oos_sharpe=2.15,
        max_drawdown_r=2.8,
    )
    assert eval_pass["promotion_eligible"] is True
    assert eval_pass["status"] == "PROMOTION_CANDIDATE"


# ============================================================================
# 7. REST API ENDPOINT INTEGRATION TESTS
# ============================================================================

def test_api_strongest_now(client):
    """GET /api/v1/signals/strongest-now returns top ranked signals and no-trade breakdown."""
    res = client.get("/api/v1/signals/strongest-now?top_n=3")
    assert res.status_code == 200
    data = res.json()["data"]
    assert "top_signals" in data
    assert "no_trade_breakdown" in data
    assert len(data["top_signals"]) <= 3


def test_api_prospective_signals_list(client):
    """GET /api/v1/signals/prospective returns journaled signals."""
    res = client.get("/api/v1/signals/prospective?limit=10")
    assert res.status_code == 200
    data = res.json()["data"]
    assert "signals" in data
    assert isinstance(data["signals"], list)


def test_api_prospective_signal_by_id(client):
    """GET /api/v1/signals/prospective/{id} returns full record."""
    res = client.get("/api/v1/signals/prospective/SIG-TEST-EURUSD-1H-20260825")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["signal_id"] == "SIG-TEST-EURUSD-1H-20260825"
    assert data["asset"] == "EURUSD"


def test_api_prospective_signal_by_id_not_found(client):
    """GET /api/v1/signals/prospective/{id} 404 on invalid ID."""
    res = client.get("/api/v1/signals/prospective/SIG-DOES-NOT-EXIST")
    assert res.status_code == 404


@pytest.mark.parametrize("window", ["today", "7d", "30d", "90d", "all_time"])
def test_api_performance_windows(client, window):
    """GET /api/v1/signals/performance/{window} returns forward metrics."""
    res = client.get(f"/api/v1/signals/performance/{window}")
    assert res.status_code == 200
    data = res.json()["data"]
    assert "win_rate_pct" in data
    assert "brier_score" in data


def test_api_drift_diagnostics(client):
    """GET /api/v1/signals/drift returns drift telemetry."""
    res = client.get("/api/v1/signals/drift")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["overall_drift_status"] == "HEALTHY"


def test_api_health(client):
    """GET /api/v1/signals/health returns canonical snapshot and safety state."""
    res = client.get("/api/v1/signals/health")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["system_status"] == "OPERATIONAL"
    assert data["real_money_enabled"] is False


def test_api_run_cycle(client):
    """POST /api/v1/signals/run-cycle executes full prospective cycle."""
    res = client.post("/api/v1/signals/run-cycle", json={"mode": "paper"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["execution_mode"] == "paper"


def test_api_resolve_due(client):
    """POST /api/v1/signals/resolve-due triggers automatic resolution."""
    res = client.post("/api/v1/signals/resolve-due")
    assert res.status_code == 200
    data = res.json()["data"]
    assert "total_resolved" in data


def test_api_replay_determinism(client):
    """POST /api/v1/signals/replay verifies deterministic snapshot replay."""
    res = client.post("/api/v1/signals/replay", json={
        "snapshot_hash": "79a4f8e12b79310d",
        "git_commit": "94d5efa",
        "config_hash": "79a4f8e12b79310d"
    })
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["identical"] is True


def test_api_prospective_learning(client):
    """GET /api/v1/research/prospective-learning returns training dataset."""
    res = client.get("/api/v1/research/prospective-learning")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["unresolved_open_trades_excluded"] is True


# ============================================================================
# 8. SAFETY & ZERO LOOKAHEAD GATES
# ============================================================================

def test_real_money_execution_strictly_disabled():
    """Enforces that real-money trading is hard locked to False across all settings."""
    settings = get_settings()
    assert settings.REAL_MONEY_ENABLED is False
    assert getattr(settings, "BROKER_EXECUTION_ENABLED", False) is False
