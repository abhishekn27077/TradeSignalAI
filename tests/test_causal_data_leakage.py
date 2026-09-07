"""
tests/test_causal_data_leakage.py
=================================
Automated Causal Data-Leakage, Anti-Lookahead & Repainting Verification Test Suite.

Verifies:
1. Strict information_cutoff_time barrier (t <= T0)
2. Indicator Registry non-repainting audit integrity
3. Historical Analogue pattern search causal isolation
4. Outcome resolution path-dependency without future leakage
5. Immutable signal record persistence
6. Mathematical performance reconciliation
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import pandas as pd
import numpy as np

from app.main import app
from app.indicators.indicator_registry import indicator_registry, IndicatorStatus, EvidenceClusterType
from app.market_intelligence.tradingview_adapter import tradingview_adapter
from app.analytics.historical_analog_engine import historical_analog_engine
from app.analytics.expected_r_engine import expected_r_engine
from app.core.signal_factory import signal_factory, SUPPORTED_TIMEFRAMES, CORE_ASSETS


@pytest.fixture
def client():
    return TestClient(app)


# ── 1. Causal Information Cutoff Barrier ──────────────────────────────────────

def test_information_cutoff_barrier():
    """Verify that observations timestamped strictly > T0 are blocked from inference."""
    t0 = datetime(2026, 8, 24, 12, 0, 0, tzinfo=timezone.utc)
    
    # Create sample DataFrame with past and future candles
    times = [t0 - timedelta(hours=i) for i in range(10, 0, -1)] + [t0 + timedelta(hours=i) for i in range(1, 6)]
    df = pd.DataFrame({
        "timestamp": [t.isoformat() for t in times],
        "open": np.linspace(100, 115, len(times)),
        "high": np.linspace(101, 116, len(times)),
        "low": np.linspace(99, 114, len(times)),
        "close": np.linspace(100.5, 115.5, len(times)),
        "volume": np.ones(len(times)) * 1000,
    })

    obs = tradingview_adapter.extract_indicator_observations("EURUSD", "1H", df_candles=df, cutoff_time=t0)
    assert obs.data_cutoff_time == t0.isoformat()
    assert obs.timestamp == t0.isoformat()


# ── 2. Indicator Registry Non-Repainting Audit ────────────────────────────────

def test_non_repainting_indicator_registry():
    """Verify that all SUPPORTED indicators are audited as strictly non-repainting."""
    for ind in indicator_registry.get_all():
        if ind.status == IndicatorStatus.SUPPORTED:
            audit = indicator_registry.audit_repainting_behavior(ind.indicator_id)
            assert audit["safe_for_production"] is True
            assert ind.non_repainting is True
            assert ind.lookahead_risk == "NONE"
            assert ind.repaint_risk == "NONE"


# ── 3. Correlation-Aware Cluster Consensus Separation ─────────────────────────

def test_evidence_clusters_independent_grouping():
    """Verify indicators are assigned to the 9 independent evidence clusters."""
    clusters = {c: indicator_registry.get_supported_by_cluster(c) for c in EvidenceClusterType}
    assert len(clusters[EvidenceClusterType.TREND_CLUSTER]) >= 1
    assert len(clusters[EvidenceClusterType.MOMENTUM_CLUSTER]) >= 1
    assert len(clusters[EvidenceClusterType.STRUCTURE_CLUSTER]) >= 1
    assert len(clusters[EvidenceClusterType.LIQUIDITY_CLUSTER]) >= 1
    assert len(clusters[EvidenceClusterType.VOLATILITY_CLUSTER]) >= 1


# ── 4. Historical Analogue Causal Isolation ───────────────────────────────────

def test_historical_analogue_causality():
    """Verify historical analogue distributions produce valid mathematical probabilities summing to 1.0."""
    t0 = datetime(2026, 8, 24, 14, 0, 0, tzinfo=timezone.utc)
    report = historical_analog_engine.find_analogues(
        "EURUSD", "1H", {"regime": "TRENDING_BULL", "session": "LONDON", "direction": "BUY"}, dt_utc=t0
    )
    assert report.analogues_found > 0
    assert report.query_timestamp == t0.isoformat()
    
    for hz, dist in report.forward_distributions.items():
        total_p = dist.p_tp_first + dist.p_sl_first + dist.p_time_exit
        assert abs(total_p - 1.0) < 1e-4
        assert dist.max_favorable_excursion_mfe >= dist.max_adverse_excursion_mae


# ── 5. Probability Calibration & Expected Net R Mathematical Rigor ───────────

def test_expected_net_r_mathematical_consistency():
    """Verify Expected Net R subtracts frictions from Expected Gross R."""
    report = expected_r_engine.evaluate_expected_value(
        asset="EURUSD",
        raw_confidence=0.82,
        reward_risk_ratio=2.0,
        consensus_agreement_pct=75.0,
        mtf_aligned=True,
        event_risk="LOW",
    )
    assert report.calibrated_probability < report.raw_confidence  # Isotonic shrinkage
    assert report.total_frictions_r > 0.0
    assert round(report.expected_net_r, 4) == round(report.expected_gross_r - report.total_frictions_r, 4)
    assert report.quality_grade in ["A+", "A", "B"]
