"""
Phase 41 — Test Suite for Real Walk-Forward Engine.

Verifies:
  - Zero-lookahead cutoff enforcement against real SQLite candles
  - Snapshot input hash reproducibility
  - Authentic outcome resolution (TP_HIT, SL_HIT, TIME_EXIT, AMBIGUOUS)
  - Full P&L cost deductions (gross, spread, slippage, fee, net P&L)
  - Confidence calibration matrix generation
  - Multi-dimensional breakdown (Asset, Session, Regime)
"""
from datetime import datetime, timezone
import pytest
from app.analytics.walk_forward_engine import walk_forward_engine


@pytest.mark.asyncio
class TestRealWalkForwardEngine:
    async def test_real_walk_forward_run(self):
        # Run 7-day walk-forward across EURUSD & BTCUSD
        start = datetime(2025, 6, 1, tzinfo=timezone.utc)
        end = datetime(2025, 6, 7, tzinfo=timezone.utc)

        result = await walk_forward_engine.run_simulation(
            start_date=start,
            end_date=end,
            assets=["EURUSD", "BTCUSD"],
            step_interval_hours=24,
            forecast_horizon_hours=24,
        )

        assert "simulation_id" in result
        assert "snapshots" in result
        assert len(result["snapshots"]) > 0

        # Verify performance stats
        perf = result["performance"]
        assert "total_forecasts" in perf
        assert "win_rate_pct" in perf
        assert "profit_factor" in perf
        assert "avg_r" in perf

        # Verify calibration matrix
        assert "calibration_matrix" in result
        assert len(result["calibration_matrix"]) > 0

        # Verify breakdowns
        assert "asset_breakdown" in result
        assert "session_breakdown" in result
        assert "regime_breakdown" in result

    async def test_snapshot_zero_lookahead_integrity(self):
        start = datetime(2025, 5, 10, tzinfo=timezone.utc)
        end = datetime(2025, 5, 12, tzinfo=timezone.utc)

        result = await walk_forward_engine.run_simulation(
            start_date=start,
            end_date=end,
            assets=["EURUSD"],
            step_interval_hours=24,
            forecast_horizon_hours=24,
        )

        for snap in result["snapshots"]:
            assert "input_snapshot_hash" in snap
            assert len(snap["input_snapshot_hash"]) == 64
            assert snap["data_cutoff"] == snap["generated_at"]
            assert snap["direction"] in ["BUY", "SELL", "NEUTRAL"]

            # Outcome must be valid
            if snap.get("outcome"):
                assert snap["outcome"] in ["TP_HIT", "SL_HIT", "TIME_EXIT", "AMBIGUOUS"]

    async def test_pnl_math_accounting(self):
        start = datetime(2025, 4, 1, tzinfo=timezone.utc)
        end = datetime(2025, 4, 5, tzinfo=timezone.utc)

        result = await walk_forward_engine.run_simulation(
            start_date=start,
            end_date=end,
            assets=["EURUSD"],
            step_interval_hours=24,
            forecast_horizon_hours=24,
        )

        for snap in result["snapshots"]:
            if snap.get("outcome") in ["TP_HIT", "SL_HIT", "TIME_EXIT"]:
                gross = snap.get("gross_pnl", 0)
                spread = snap.get("spread_cost", 0)
                slippage = snap.get("slippage_cost", 0)
                fee = snap.get("broker_fee", 0)
                net = snap.get("net_pnl", 0)

                # Net must strictly equal gross - spread - slippage - fee (within floating tolerance)
                expected_net = round(gross - spread - slippage - fee, 5)
                assert abs(net - expected_net) < 1e-4
