"""
Phase 40 — Walk-Forward Engine Tests.

Tests:
  1. Zero lookahead enforcement
  2. Forecast snapshot immutability & input hash verification
  3. Outcome resolution (TP_HIT, SL_HIT, TIME_EXIT, AMBIGUOUS)
  4. P&L math (gross, spread, slippage, fee, net, R-multiple)
  5. Confidence calibration matrix structure
  6. Performance statistics computation
"""
import pytest
from datetime import datetime, timedelta, timezone


@pytest.fixture
def walk_forward_engine():
    from app.analytics.walk_forward_engine import WalkForwardEngine
    return WalkForwardEngine()


class TestWalkForwardEngine:
    """Tests for the walk-forward simulation engine."""

    @pytest.mark.asyncio
    async def test_simulation_runs_without_error(self, walk_forward_engine):
        """Basic smoke test: simulation runs and returns expected structure."""
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 1, 5, tzinfo=timezone.utc)

        result = await walk_forward_engine.run_simulation(
            start_date=start,
            end_date=end,
            assets=["EURUSD", "BTCUSD"],
            step_interval_hours=24,
            forecast_horizon_hours=24,
        )

        assert "simulation_id" in result
        assert "snapshots" in result
        assert "performance" in result
        assert "calibration_matrix" in result
        assert "asset_breakdown" in result
        assert result["total_snapshots"] > 0

    @pytest.mark.asyncio
    async def test_zero_lookahead_data_cutoff(self, walk_forward_engine):
        """Verify that data cutoff equals evaluation time (zero lookahead)."""
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 1, 3, tzinfo=timezone.utc)

        result = await walk_forward_engine.run_simulation(
            start_date=start,
            end_date=end,
            assets=["EURUSD"],
            step_interval_hours=24,
        )

        for snap in result["snapshots"]:
            # data_cutoff must equal generated_at (zero lookahead)
            assert snap["data_cutoff"] == snap["generated_at"], \
                f"Lookahead violation: cutoff={snap['data_cutoff']} != generated={snap['generated_at']}"

    @pytest.mark.asyncio
    async def test_snapshot_has_immutable_fields(self, walk_forward_engine):
        """Verify each snapshot has all required immutable fields."""
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 1, 2, tzinfo=timezone.utc)

        result = await walk_forward_engine.run_simulation(
            start_date=start,
            end_date=end,
            assets=["EURUSD"],
        )

        required_fields = [
            "forecast_id", "asset", "direction", "confidence",
            "input_snapshot_hash", "generated_at", "forecast_for",
        ]
        for snap in result["snapshots"]:
            for field in required_fields:
                assert field in snap, f"Missing field: {field}"
                assert snap[field] is not None, f"Field is None: {field}"

    @pytest.mark.asyncio
    async def test_input_hash_reproducibility(self, walk_forward_engine):
        """Verify same input produces same hash across runs."""
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 1, 2, tzinfo=timezone.utc)

        r1 = await walk_forward_engine.run_simulation(start_date=start, end_date=end, assets=["EURUSD"])
        r2 = await walk_forward_engine.run_simulation(start_date=start, end_date=end, assets=["EURUSD"])

        h1 = {s["forecast_id"][:20]: s["input_snapshot_hash"] for s in r1["snapshots"]}
        h2 = {s["forecast_id"][:20]: s["input_snapshot_hash"] for s in r2["snapshots"]}

        # Same asset+time should produce same input hash
        for snap in r1["snapshots"]:
            key = f"{snap['asset']}-{snap['generated_at']}"
            matching = [s for s in r2["snapshots"]
                        if s["asset"] == snap["asset"] and s["generated_at"] == snap["generated_at"]]
            if matching:
                assert snap["input_snapshot_hash"] == matching[0]["input_snapshot_hash"]

    @pytest.mark.asyncio
    async def test_outcome_resolution_values(self, walk_forward_engine):
        """Verify outcome values are valid."""
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 1, 5, tzinfo=timezone.utc)

        result = await walk_forward_engine.run_simulation(
            start_date=start, end_date=end, assets=["EURUSD", "BTCUSD"],
        )

        valid_outcomes = {"TP_HIT", "SL_HIT", "TIME_EXIT", "AMBIGUOUS"}
        for snap in result["snapshots"]:
            assert snap["outcome"] in valid_outcomes, f"Invalid outcome: {snap['outcome']}"

    @pytest.mark.asyncio
    async def test_pnl_math_consistency(self, walk_forward_engine):
        """Verify net_pnl = gross_pnl - spread - slippage - fee."""
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 1, 3, tzinfo=timezone.utc)

        result = await walk_forward_engine.run_simulation(
            start_date=start, end_date=end, assets=["EURUSD"],
        )

        for snap in result["snapshots"]:
            if snap["outcome"] != "AMBIGUOUS":
                expected_net = snap["gross_pnl"] - snap["spread_cost"] - snap["slippage_cost"] - snap["broker_fee"]
                assert abs(snap["net_pnl"] - expected_net) < 1e-8, \
                    f"P&L inconsistency: net={snap['net_pnl']} expected={expected_net}"

    @pytest.mark.asyncio
    async def test_calibration_matrix_structure(self, walk_forward_engine):
        """Verify calibration matrix has expected buckets."""
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 1, 10, tzinfo=timezone.utc)

        result = await walk_forward_engine.run_simulation(
            start_date=start, end_date=end, assets=["EURUSD"],
        )

        matrix = result["calibration_matrix"]
        assert len(matrix) == 6, f"Expected 6 calibration buckets, got {len(matrix)}"

        for bucket in matrix:
            assert "bucket" in bucket
            assert "predicted_confidence" in bucket
            assert "actual_win_rate" in bucket
            assert "sample_size" in bucket

    @pytest.mark.asyncio
    async def test_performance_stats_keys(self, walk_forward_engine):
        """Verify performance stats have all required keys."""
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 1, 5, tzinfo=timezone.utc)

        result = await walk_forward_engine.run_simulation(
            start_date=start, end_date=end, assets=["EURUSD"],
        )

        perf = result["performance"]
        required = [
            "total_forecasts", "resolved", "win_rate_pct",
            "profit_factor", "expectancy", "avg_r", "directional_accuracy_pct",
        ]
        for key in required:
            assert key in perf, f"Missing perf key: {key}"

    @pytest.mark.asyncio
    async def test_asset_breakdown(self, walk_forward_engine):
        """Verify per-asset breakdown includes all simulated assets."""
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 1, 3, tzinfo=timezone.utc)
        assets = ["EURUSD", "BTCUSD", "XAUUSD"]

        result = await walk_forward_engine.run_simulation(
            start_date=start, end_date=end, assets=assets,
        )

        breakdown = result["asset_breakdown"]
        for asset in assets:
            assert asset in breakdown, f"Missing asset in breakdown: {asset}"
            assert "win_rate_pct" in breakdown[asset]
            assert "total_net_pnl" in breakdown[asset]
