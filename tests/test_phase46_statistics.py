"""
Phase 46 — Test Suite for Null Hypothesis Significance Testing.

Verifies:
  - H0 (Net R <= 0) vs H1 (Net R > 0)
  - t-statistic, standard error, p-value, Cohen's d effect size
"""
import pytest
from app.analytics.live_edge_validation_engine import live_edge_validation_engine


class TestNullHypothesisTesting:
    def test_insufficient_sample_hypothesis_fallback(self):
        res = live_edge_validation_engine.perform_null_hypothesis_testing(trades=[])
        assert res["status"] == "INSUFFICIENT_SAMPLE_FOR_INFERENCE"

    def test_hypothesis_computation_with_data(self):
        trades = [{"net_r": 1.8}] * 20 + [{"net_r": -1.1}] * 10
        res = live_edge_validation_engine.perform_null_hypothesis_testing(trades=trades)
        assert res["status"] == "TESTED"
        assert "t_statistic" in res
        assert "p_value_one_tailed" in res
        assert "cohens_d" in res
        assert res["sample_mean_r"] > 0
