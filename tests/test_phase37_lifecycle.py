import pytest
from app.forecast_engine.lifecycle import PredictionLifecycleManager


def test_lifecycle_state_definitions():
    mgr = PredictionLifecycleManager()
    assert hasattr(mgr, "process_outcomes") or hasattr(mgr, "start")
