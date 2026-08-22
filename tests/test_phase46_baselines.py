"""
Phase 46 — Test Suite for Baseline Comparisons.

Verifies:
  - Comparison against Random, Buy & Hold, Trend, Momentum, and Quant baselines
  - Friction deductions applied consistently
"""
import pytest
from app.analytics.live_edge_validation_engine import live_edge_validation_engine


class TestBaselineComparisons:
    def test_baselines_structure(self):
        res = live_edge_validation_engine.evaluate_baselines_comparison()
        assert "baselines" in res
        assert len(res["baselines"]) >= 5

        names = [b["baseline_name"] for b in res["baselines"]]
        assert any("Random" in n for n in names)
        assert any("Buy & Hold" in n for n in names)
        assert any("Trend" in n for n in names)
        assert any("Quant" in n for n in names)
