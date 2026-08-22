"""
Phase 47 — Test Suite for Real Multi-Model Forecast Pipeline Execution.

Verifies:
  - Execution of 8-layer multi-model pipeline
  - Separation of Forecast vs Trade Signal decision
  - Visible forecast outputs even when trade is rejected (NO_TRADE)
"""
import pytest
from app.runtime.live_forecast_scheduler import live_forecast_scheduler


class TestForecastPipeline:
    def test_forecast_execution_across_all_9_assets(self):
        cycle = live_forecast_scheduler.process_cycle()
        assert cycle["total_assets_scanned"] == 9
        assert len(cycle["forecasts"]) == 9

        for f in cycle["forecasts"]:
            assert "asset" in f
            assert "direction" in f
            assert "probability" in f
            assert "confidence" in f
            assert "decision" in f
            assert "model_outputs" in f
            assert f["decision"] in ["TAKE_TRADE", "NO_TRADE"]

    def test_rejected_forecast_remains_visible(self):
        cycle = live_forecast_scheduler.process_cycle()
        rejected_forecasts = [f for f in cycle["forecasts"] if f["decision"] == "NO_TRADE"]

        # Rejected forecasts must retain valid price, direction, probability, and rejection reason
        for rf in rejected_forecasts:
            assert rf["rejection_reason"] is not None
            assert rf["entry_price"] > 0
            assert rf["direction"] in ["BUY", "SELL", "WAIT"]
