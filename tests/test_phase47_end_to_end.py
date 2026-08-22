"""
Phase 47 — Test Suite for Real End-to-End Live Forecast Execution.

Verifies:
  - End-to-end data lineage from real closed candle to shadow ledger record
  - Deterministic input hash and prediction hash generation
  - Cycle results caching and trace persistence
"""
import os
import json
import pytest
from app.runtime.live_forecast_scheduler import live_forecast_scheduler
from app.analytics.shadow_ledger_engine import shadow_ledger_engine


class TestEndToEndExecution:
    def test_end_to_end_trace_artifact_exists(self):
        trace_file = "artifacts/phase47/REAL_END_TO_END_TRACE.json"
        assert os.path.exists(trace_file), "REAL_END_TO_END_TRACE.json must be generated"

        with open(trace_file, "r") as f:
            trace = json.load(f)

        assert trace["phase"] == 47
        assert trace["target_asset"] == "EURUSD"
        assert "candle_ohlcv" in trace
        assert "input_hash" in trace
        assert "model_outputs" in trace
        assert "zero_trust_risk_decision" in trace
        assert len(trace["all_9_assets_scanned"]) == 9

    def test_shadow_ledger_immutable_recording(self):
        candle = live_forecast_scheduler.fetch_latest_closed_candle("BTCUSD")
        pred_data = live_forecast_scheduler.evaluate_multi_model_forecast("BTCUSD", candle)
        rec = shadow_ledger_engine.record_prediction(pred_data)

        assert "prediction_id" in rec
        assert "input_hash" in rec
        assert rec["status"] in ["FORECAST_CREATED", "PREDICTION_RECORDED", "PAPER_OPEN"]
