"""
Phase 46 — Test Suite for Live Model Contribution and Forward Ablation.

Verifies:
  - Strict separation of OOS vs Live model contributions
  - 'NOT_YET_ESTIMABLE' state when sample size is developing
"""
import pytest
from app.analytics.live_edge_validation_engine import live_edge_validation_engine


class TestLiveModelContribution:
    def test_live_model_contribution_isolation(self):
        res = live_edge_validation_engine.evaluate_live_model_contribution()
        assert "models" in res
        assert len(res["models"]) == 9

        for m in res["models"]:
            assert "model" in m
            assert "oos_accuracy" in m
            assert "live_contribution" in m
            assert "NOT_YET_ESTIMABLE" in m["live_contribution"]
