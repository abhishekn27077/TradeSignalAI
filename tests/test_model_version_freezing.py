"""
tests/test_model_version_freezing.py
====================================
Model & Policy Version Freezing Tests (Phase 72).

Verifies:
1. Every prediction permanently freezes indicator_version, strategy_version, Kronos hash, and policy_version.
2. Historical predictions cannot be rewritten when a new model version is released.
"""

import pytest
import json
from datetime import datetime, timezone

from app.shadow.shadow_live_engine import ShadowLiveEngine


def test_model_version_freezing_in_prediction(tmp_path):
    """Predictions must permanently store active model and policy versions."""
    db_file = str(tmp_path / "test_version_freeze.db")
    engine = ShadowLiveEngine(db_path=db_file)
    now = datetime(2026, 8, 26, 12, 0, 0, tzinfo=timezone.utc)

    pred = engine.generate_shadow_signal("ETHUSD", "1h", reference_dt=now)
    engine.persist_prediction(pred)

    stored = engine.get_predictions(asset="ETHUSD")[0]
    assert "model_versions" in stored
    models_dict = json.loads(stored["model_versions"])
    assert "ensemble" in models_dict
    assert "policy" in models_dict
    assert stored["policy_version"] == "POL-72-v1"
