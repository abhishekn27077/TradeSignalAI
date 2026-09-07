"""
tests/test_deterministic_signal_reproduction.py
===============================================
Deterministic Signal Reproduction Tests (Phase 72).

Verifies:
1. Two identical input data snapshots produce identical cryptographic SHA-256 hashes.
2. Generating a shadow signal on the exact same snapshot reproduces the exact same prediction_id, direction, entry, SL, and TP.
3. Decision reproducibility persists across server / engine restarts.
"""

import pytest
import pandas as pd
from datetime import datetime, timezone

from app.core.data_snapshot_service import data_snapshot_service
from app.shadow.shadow_live_engine import ShadowLiveEngine


def test_data_snapshot_cryptographic_parity():
    """Identical market data frames must produce identical SHA-256 snapshot hashes."""
    t0 = datetime(2026, 8, 26, 12, 0, 0, tzinfo=timezone.utc)
    df = pd.DataFrame({
        "open": [1.0800, 1.0810, 1.0820],
        "high": [1.0850, 1.0860, 1.0870],
        "low": [1.0790, 1.0800, 1.0810],
        "close": [1.0840, 1.0850, 1.0860],
        "volume": [1000, 1500, 2000]
    })

    models = {"kronos": "v1", "policy": "POL-72-v1"}
    snap1 = data_snapshot_service.create_snapshot_id(df, "EURUSD", "1h", t0, models, "POL-72-v1")
    snap2 = data_snapshot_service.create_snapshot_id(df, "EURUSD", "1h", t0, models, "POL-72-v1")

    assert snap1["snapshot_hash"] == snap2["snapshot_hash"]
    assert snap1["snapshot_id"] == snap2["snapshot_id"]
    assert data_snapshot_service.verify_reproducibility(snap1["canonical_payload"], snap2["canonical_payload"]) is True


def test_deterministic_signal_reproduction_across_runs(tmp_path):
    """Running signal generation on the same historical freeze twice yields identical decisions."""
    db_file = str(tmp_path / "test_reproduce.db")
    engine1 = ShadowLiveEngine(db_path=db_file)
    t0 = datetime(2026, 8, 26, 12, 0, 0, tzinfo=timezone.utc)

    sig1 = engine1.generate_shadow_signal("EURUSD", "1h", reference_dt=t0)
    
    del engine1
    engine2 = ShadowLiveEngine(db_path=db_file)
    sig2 = engine2.generate_shadow_signal("EURUSD", "1h", reference_dt=t0)

    assert sig1.prediction_id == sig2.prediction_id
    assert sig1.direction == sig2.direction
    assert sig1.entry == sig2.entry
    assert sig1.stop_loss == sig2.stop_loss
    assert sig1.take_profit == sig2.take_profit
    assert sig1.decision_hash == sig2.decision_hash
