"""
Phase 46 — Test Suite for Multi-Dimensional Robustness.

Verifies:
  - 9-Asset Robustness breakdown
  - 5-Regime Robustness breakdown
  - 4-Session Robustness breakdown
"""
import pytest
from app.analytics.live_edge_validation_engine import live_edge_validation_engine, CORE_ASSETS, MARKET_REGIMES, TRADING_SESSIONS


class TestRobustnessBreakdowns:
    def test_multi_dimensional_robustness_structures(self):
        rob = live_edge_validation_engine.evaluate_multi_dimensional_robustness()
        assert "assets" in rob
        assert "regimes" in rob
        assert "sessions" in rob

        assert len(rob["assets"]) == 9
        assert len(rob["regimes"]) == 5
        assert len(rob["sessions"]) == 4

        for a in rob["assets"]:
            assert a["asset"] in CORE_ASSETS
            assert "sample_size" in a

        for r in rob["regimes"]:
            assert r["regime"] in MARKET_REGIMES

        for s in rob["sessions"]:
            assert s["session"] in TRADING_SESSIONS
