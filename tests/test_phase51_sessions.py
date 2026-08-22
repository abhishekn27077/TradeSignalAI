import pytest
import pandas as pd
from datetime import datetime, timezone, timedelta

from app.strategies.Session.session_engine import (
    SessionEngine, SessionProfile, SessionName
)


def test_session_engine_killzones():
    engine = SessionEngine()

    # Test London Open (08:00 UTC)
    t_london = datetime(2026, 8, 3, 8, 30, tzinfo=timezone.utc)
    res_london = engine.evaluate_session(current_time=t_london)

    assert res_london.session_name == SessionName.LONDON
    assert res_london.is_killzone is True
    assert res_london.is_active is True

    # Test New York AM (13:30 UTC)
    t_ny = datetime(2026, 8, 3, 13, 30, tzinfo=timezone.utc)
    res_ny = engine.evaluate_session(current_time=t_ny)

    assert res_ny.session_name == SessionName.NEW_YORK_AM
    assert res_ny.is_killzone is True

    # Test Asia Session (03:00 UTC)
    t_asia = datetime(2026, 8, 3, 3, 0, tzinfo=timezone.utc)
    res_asia = engine.evaluate_session(current_time=t_asia)

    assert res_asia.session_name == SessionName.ASIA
    assert res_asia.is_active is True
