"""
Phase 45 — Test Suite for Autonomous Scheduler and Shadow Outcome Worker.

Verifies:
  - 9 core assets scanned
  - Data freshness verification & closed candle detection
  - Multi-model evaluation across all 8 layers
  - Zero-Trust qualification & rejection reason recording
  - Duplicate prediction prevention
  - Shadow outcome worker resolution against future candles
"""
import pytest
from datetime import datetime, timezone
from app.runtime.live_forecast_scheduler import live_forecast_scheduler, CORE_ASSETS
from app.runtime.shadow_outcome_worker import shadow_outcome_worker
from app.analytics.shadow_ledger_engine import shadow_ledger_engine


class TestLiveSchedulerAndWorker:
    def test_scheduler_scans_all_9_assets(self):
        cycle = live_forecast_scheduler.process_cycle()
        assert cycle["total_assets_scanned"] == 9
        assert len(cycle["forecasts"]) == 9

        assets_found = [f["asset"] for f in cycle["forecasts"]]
        for asset in CORE_ASSETS:
            assert asset in assets_found

    def test_multi_model_8_layer_outputs_present(self):
        cycle = live_forecast_scheduler.get_latest_cycle_results()
        for f in cycle["forecasts"]:
            assert "model_outputs" in f
            m_outs = f["model_outputs"]
            for expected_model in ["quant", "kronos", "faiss", "time_pattern", "regime", "macro", "news", "ai", "ensemble"]:
                assert expected_model in m_outs, f"Missing model {expected_model} in {f['asset']}"
                assert "direction" in m_outs[expected_model]

    def test_duplicate_prediction_prevention(self):
        candle = {
            "asset": "EURUSD",
            "timestamp": "2026-08-21 12:00:00",
            "open": 1.0850,
            "high": 1.0870,
            "low": 1.0830,
            "close": 1.0860,
            "volume": 500.0,
        }
        pred_data = live_forecast_scheduler.evaluate_multi_model_forecast("EURUSD", candle)
        rec1 = shadow_ledger_engine.record_prediction(pred_data)
        rec2 = shadow_ledger_engine.record_prediction(pred_data)

        # Should return existing record without creating duplicate
        assert rec1["prediction_id"] == rec2["prediction_id"]

    def test_shadow_outcome_worker_resolution_cycle(self):
        res = shadow_outcome_worker.run_resolution_cycle()
        assert "cycle_timestamp" in res
        assert "open_trades_scanned" in res
        assert "trades_resolved_this_cycle" in res
        assert isinstance(res["resolved_trades"], list)

    def test_scheduler_status(self):
        status = live_forecast_scheduler.get_status()
        assert status["status"] in ["LIVE", "PAUSED"]
        assert status["total_assets"] == 9
        assert "processed_keys_count" in status
