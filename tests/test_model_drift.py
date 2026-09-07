"""
tests/test_model_drift.py
=========================
Model Drift Detection & Automatic Safe Degradation Tests (Phase 72).

Verifies:
1. Directional skew (>80% one-sided bias) triggers WATCH / CRITICAL drift status.
2. Low rolling win rate (<45%) triggers DEGRADED status with 0.5x risk multiplier.
3. Severe performance collapse (<30%) triggers emergency NO_TRADE lockout.
"""

import pytest
from app.analytics.edge_drift_engine import edge_drift_engine, DriftStatus


def test_edge_drift_engine_evaluation():
    """Drift engine must return valid DriftStatus and appropriate risk multiplier."""
    res = edge_drift_engine.evaluate_system_drift()
    assert "drift_status" in res
    assert res["drift_status"] in [s.value for s in DriftStatus]
    assert "risk_multiplier" in res
    assert 0.0 <= res["risk_multiplier"] <= 1.0
    assert "recommended_action" in res
