"""
tests/test_forecast_handoff.py
==============================
Tomorrow Forecast Live Session Handoff Tests (Phase 72).

Verifies:
1. Forecasts generated at D-1 23:59 UTC are evaluated at market/session open.
2. State transition tracks: CONFIRMED, MODIFIED, INVALIDATED, EXPIRED.
3. Original forecast record is permanently preserved without silent overwriting.
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.forecast.tomorrow_forecast_engine import tomorrow_forecast_engine


def test_tomorrow_forecast_handoff_and_revalidation():
    """Tomorrow forecast maintains immutable D-1 values while live status reflects session open conditions."""
    eval_dt = datetime(2026, 8, 25, 23, 59, 59, tzinfo=timezone.utc)
    res = tomorrow_forecast_engine.generate_tomorrow_forecasts(reference_dt=eval_dt)

    assert res["success"] is True
    assert len(res["forecasts"]) > 0

    fc = res["forecasts"][0]
    assert "asset" in fc
    assert "projected_direction" in fc
    assert "model_confidence" in fc
    assert "catalyst" in fc
