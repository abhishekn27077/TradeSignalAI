"""
Phase 46 — Test Suite for Edge Drift & Model Drift Detection.

Verifies:
  - Rolling windows evaluation (Last 20, 50, 100, 200, All)
  - Early vs recent cohort drift analysis
  - Model drift warning detection
"""
import pytest
from app.analytics.edge_drift_engine import edge_drift_engine


class TestDriftDetection:
    def test_rolling_windows_structure(self):
        res = edge_drift_engine.evaluate_rolling_windows()
        assert "windows" in res
        assert len(res["windows"]) == 5

    def test_edge_drift_states(self):
        res = edge_drift_engine.detect_edge_drift()
        assert "drift_status" in res
        assert res["drift_status"] in ["IMPROVING", "STABLE", "DEGRADING", "INSUFFICIENT_DATA"]

    def test_model_drift_detection(self):
        res = edge_drift_engine.detect_model_drift()
        assert "model_drift_warning" in res
        assert "buy_sell_balance" in res
        assert "status" in res
