"""
tests/test_forecast_immutability.py
===================================
Prediction Immutability & Revision History Tests (Phase 72).

Verifies:
1. Predictions persisted to shadow_predictions cannot be overwritten to match reality.
2. Attempting to change an existing prediction creates a new revision with supersedes_id.
"""

import pytest
import sqlite3
from datetime import datetime, timezone

from app.shadow.shadow_live_engine import ShadowLiveEngine, ShadowPrediction


def test_shadow_prediction_immutability(tmp_path):
    """Once written, a historical prediction's entry, SL, and TP cannot be updated."""
    db_file = str(tmp_path / "test_immutable.db")
    engine = ShadowLiveEngine(db_path=db_file)
    now = datetime(2026, 8, 26, 12, 0, 0, tzinfo=timezone.utc)

    pred = engine.generate_shadow_signal("EURUSD", "1h", reference_dt=now)
    assert engine.persist_prediction(pred) is True

    # Attempting to re-insert identical prediction does not change original values
    pred_modified = ShadowPrediction(**{**pred.to_dict(), "entry": 9.9999})
    engine.persist_prediction(pred_modified)

    stored = engine.get_predictions(asset="EURUSD")
    assert len(stored) == 1
    assert stored[0]["entry"] == pred.entry  # Original preserved


def test_prediction_revisioning_via_supersedes_id(tmp_path):
    """Revising a prediction marks the previous prediction as SUPERSEDED."""
    db_file = str(tmp_path / "test_rev.db")
    engine = ShadowLiveEngine(db_path=db_file)
    now = datetime(2026, 8, 26, 12, 0, 0, tzinfo=timezone.utc)

    pred1 = engine.generate_shadow_signal("GBPUSD", "1h", reference_dt=now)
    engine.persist_prediction(pred1)

    pred2_id = f"{pred1.prediction_id}-rev2"
    pred2 = ShadowPrediction(**{**pred1.to_dict(), "prediction_id": pred2_id, "supersedes_id": pred1.prediction_id})
    engine.persist_prediction(pred2, supersedes_id=pred1.prediction_id)

    all_preds = engine.get_predictions(asset="GBPUSD")
    p1 = [p for p in all_preds if p["prediction_id"] == pred1.prediction_id][0]
    p2 = [p for p in all_preds if p["prediction_id"] == pred2_id][0]

    assert p1["status"] == "SUPERSEDED"
    assert p2["supersedes_id"] == pred1.prediction_id
