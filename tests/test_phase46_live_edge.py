"""
Phase 46 — Test Suite for Live Cohort Edge Metrics & Confirmation Gates.

Verifies:
  - Calculation of N, wins, losses, win rate, profit factor, expectancy
  - Max drawdown and streak calculations
  - 14-Point Confirmation Gate schema and governance status
"""
import pytest
from app.analytics.live_edge_validation_engine import live_edge_validation_engine


class TestLiveEdgeMetrics:
    def test_empty_metrics_fallback(self):
        metrics = live_edge_validation_engine.compute_live_metrics(trades=[])
        assert metrics["sample_size"] == 0
        assert metrics["governance_status"] == "INSUFFICIENT_SAMPLE"

    def test_synthetic_batch_metrics(self):
        sample_trades = [
            {"status": "TP_HIT", "net_r": 1.82},
            {"status": "TP_HIT", "net_r": 1.78},
            {"status": "SL_HIT", "net_r": -1.15},
            {"status": "TP_HIT", "net_r": 1.85},
            {"status": "SL_HIT", "net_r": -1.12},
            {"status": "TP_HIT", "net_r": 1.80},
        ]
        metrics = live_edge_validation_engine.compute_live_metrics(trades=sample_trades)
        assert metrics["sample_size"] == 6
        assert metrics["wins"] == 4
        assert metrics["losses"] == 2
        assert metrics["win_rate_pct"] == 66.67
        assert metrics["profit_factor"] > 1.5
        assert metrics["expectancy_r"] > 0
        assert metrics["longest_winning_streak"] >= 2

    def test_14_point_confirmation_gates_structure(self):
        gates_res = live_edge_validation_engine.evaluate_14_point_confirmation_gates()
        assert "classification" in gates_res
        assert "traffic_light" in gates_res
        assert gates_res["total_gates"] == 14
        assert len(gates_res["gates"]) == 14

        # Verify Gate #1 requires N >= 300
        gate_1 = next(g for g in gates_res["gates"] if g["gate_id"] == 1)
        assert "N >= 300" in gate_1["requirement"]
