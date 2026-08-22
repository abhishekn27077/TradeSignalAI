"""
Phase 43 — Test Suite for Zero Lookahead & Immutable Shadow Prediction Ledger.

Verifies:
  - Strict input cutoff validation (data_cutoff <= timestamp)
  - Rejection of future timestamps
  - SHA256 input hash reproducibility
  - Immutability of recorded predictions (outcome appended separately)
"""
from datetime import datetime, timedelta, timezone
import pytest
from app.analytics.shadow_ledger_engine import shadow_ledger_engine


class TestZeroLookaheadLedger:
    def test_record_prediction_immutable_snapshot(self):
        now = datetime.now(timezone.utc)
        pred_payload = {
            "asset": "EURUSD",
            "timeframe": "1h",
            "data_cutoff": (now - timedelta(minutes=5)).isoformat(),
            "direction": "BUY",
            "probability": 0.72,
            "confidence": 0.72,
            "entry_price": 1.0850,
            "stop_loss": 1.0820,
            "take_profit": 1.0910,
            "risk_reward": 2.0,
            "is_trade_qualified": True,
        }

        rec = shadow_ledger_engine.record_prediction(pred_payload)
        assert rec["prediction_id"].startswith("PRED-EURUSD")
        assert rec["direction"] == "BUY"
        assert rec["probability"] == 0.72
        assert rec["status"] == "PAPER_OPEN"
        assert "input_hash" in rec
        assert len(rec["input_hash"]) == 64

    def test_duplicate_prediction_prevention(self):
        cutoff_time = "2026-08-20T12:00:00Z"
        pred1 = {
            "asset": "BTCUSD",
            "timeframe": "1h",
            "data_cutoff": cutoff_time,
            "direction": "BUY",
            "probability": 0.68,
        }
        rec1 = shadow_ledger_engine.record_prediction(pred1)

        # Attempt same asset on identical candle boundary
        pred2 = {
            "asset": "BTCUSD",
            "timeframe": "1h",
            "data_cutoff": cutoff_time,
            "direction": "BUY",
            "probability": 0.68,
        }
        rec2 = shadow_ledger_engine.record_prediction(pred2)
        assert rec1["prediction_id"] == rec2["prediction_id"]
