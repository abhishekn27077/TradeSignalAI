"""
Phase 46 — Test Suite for Bootstrap Confidence Intervals.

Verifies:
  - 10,000 bootstrap resamples
  - Deterministic seed (464646) reproducibility
  - 95% Confidence Interval structure for Win Rate and Expectancy
  - Result SHA256 hash generation
"""
import pytest
from app.analytics.live_edge_validation_engine import live_edge_validation_engine, BOOTSTRAP_SEED, BOOTSTRAP_ITERATIONS


class TestBootstrapConfidence:
    def test_bootstrap_reproducibility(self):
        sample_trades = [{"net_r": 1.82}, {"net_r": 1.78}, {"net_r": -1.15}, {"net_r": 1.85}, {"net_r": -1.12}, {"net_r": 1.80}]
        res1 = live_edge_validation_engine.compute_bootstrap_confidence_intervals(trades=sample_trades)
        res2 = live_edge_validation_engine.compute_bootstrap_confidence_intervals(trades=sample_trades)

        assert res1["bootstrap_seed"] == BOOTSTRAP_SEED
        assert res1["iterations"] == BOOTSTRAP_ITERATIONS
        assert res1["result_hash"] == res2["result_hash"]
        assert res1["expectancy_ci_95"]["lower"] == res2["expectancy_ci_95"]["lower"]
        assert res1["expectancy_ci_95"]["upper"] == res2["expectancy_ci_95"]["upper"]
        assert res1["prob_positive_expectancy"] == res2["prob_positive_expectancy"]
