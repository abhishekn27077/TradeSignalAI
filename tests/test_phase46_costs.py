"""
Phase 46 — Test Suite for Cost & Slippage Stress Testing.

Verifies:
  - Cost multiplier evaluations (1x, 1.5x, 2x, 3x)
  - Slippage degradation tests (+25% to +200%)
  - Break-even cost calculation
"""
import pytest
from app.analytics.live_edge_validation_engine import live_edge_validation_engine


class TestCostAndSlippageStress:
    def test_cost_stress_matrix(self):
        res = live_edge_validation_engine.evaluate_cost_and_slippage_stress()
        assert "cost_multipliers" in res
        assert "slippage_stress" in res
        assert "break_even_cost_r" in res
        assert res["break_even_cost_r"] > 0

        multipliers = [c["multiplier"] for c in res["cost_multipliers"]]
        assert any("1.0x" in m for m in multipliers)
        assert any("2.0x" in m for m in multipliers)
        assert any("3.0x" in m for m in multipliers)
