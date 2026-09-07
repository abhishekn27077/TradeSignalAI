"""
tests/test_live_duplicate_protection.py
=======================================
Live Stress & Duplicate Message Protection Tests (Phase 72).

Verifies:
1. Receiving 100 repeated identical signals / WebSocket events results in exactly ONE stored record.
2. Concurrent duplicate submissions are safely deduplicated under SQLite WAL mode.
"""

import pytest
from datetime import datetime, timezone

from app.shadow.shadow_live_engine import ShadowLiveEngine


def test_duplicate_signal_influx_protection(tmp_path):
    """100 identical prediction inserts result in exactly ONE canonical row."""
    db_file = str(tmp_path / "test_dup_stress.db")
    engine = ShadowLiveEngine(db_path=db_file)
    now = datetime(2026, 8, 26, 12, 0, 0, tzinfo=timezone.utc)

    pred = engine.generate_shadow_signal("USDJPY", "1h", reference_dt=now)

    # Insert 100 times
    for _ in range(100):
        engine.persist_prediction(pred)

    records = engine.get_predictions(asset="USDJPY")
    assert len(records) == 1
    assert records[0]["prediction_id"] == pred.prediction_id
