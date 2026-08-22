"""
tests/test_phase33_timing.py
Phase 33 — CandleClock and CandleDisciplineChecker tests.
"""
import pytest
import pandas as pd
from datetime import datetime, timezone, timedelta

from app.core.timing import CandleClock, ISTConverter
from app.core.candle_discipline import CandleDisciplineChecker, CandleDisciplineViolation


class TestCandleClock:

    def test_h4_boundary_is_multiple_of_4_hours(self):
        now = datetime(2026, 8, 19, 13, 45, 0, tzinfo=timezone.utc)
        status = CandleClock.get_candle_status("H4", reference_time=now)
        # Current candle opens at 12:00 UTC
        open_str = status["current_candle_open_utc"]
        open_dt = datetime.fromisoformat(open_str)
        assert open_dt.hour % 4 == 0
        assert open_dt.minute == 0
        assert open_dt.second == 0

    def test_h1_remaining_is_positive(self):
        now = datetime(2026, 8, 19, 13, 45, 0, tzinfo=timezone.utc)
        status = CandleClock.get_candle_status("H1", reference_time=now)
        assert status["remaining_seconds"] > 0
        assert status["remaining_seconds"] <= 3600

    def test_d1_candle_boundary(self):
        now = datetime(2026, 8, 19, 6, 0, 0, tzinfo=timezone.utc)
        status = CandleClock.get_candle_status("D1", reference_time=now)
        open_str = status["current_candle_open_utc"]
        open_dt = datetime.fromisoformat(open_str)
        assert open_dt.hour == 0
        assert open_dt.minute == 0

    def test_countdown_format(self):
        now = datetime(2026, 8, 19, 13, 45, 0, tzinfo=timezone.utc)
        status = CandleClock.get_candle_status("H4", reference_time=now)
        countdown = status["countdown"]
        parts = countdown.split(":")
        assert len(parts) == 3

    def test_ist_conversion(self):
        utc_dt = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)
        ist_str = ISTConverter.to_ist_string(utc_dt)
        # IST is UTC+5:30
        assert "IST" in ist_str
        assert "17:30" in ist_str  # 12:00 UTC = 17:30 IST

    def test_unsupported_timeframe_raises(self):
        with pytest.raises(ValueError):
            CandleClock.get_candle_status("M99")


class TestCandleDiscipline:

    def _make_df(self, start: datetime, periods: int, freq: str) -> pd.DataFrame:
        idx = pd.date_range(start=start, periods=periods, freq=freq, tz="UTC")
        return pd.DataFrame({"close": range(periods), "high": range(periods), "low": range(periods)}, index=idx)

    def test_passes_when_all_rows_before_prediction(self):
        prediction_ts = datetime(2026, 8, 19, 16, 0, 0, tzinfo=timezone.utc)
        df = self._make_df(datetime(2026, 8, 19, 8, 0, 0, tzinfo=timezone.utc), periods=8, freq="h")
        result = CandleDisciplineChecker.validate(df, prediction_ts)
        assert result.passed is True
        assert result.violating_rows == 0

    def test_fails_when_row_equals_prediction(self):
        prediction_ts = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)
        df = self._make_df(datetime(2026, 8, 19, 8, 0, 0, tzinfo=timezone.utc), periods=5, freq="h")
        # Row at 12:00 is >= prediction_ts
        result = CandleDisciplineChecker.validate(df, prediction_ts)
        assert result.passed is False
        assert result.violating_rows > 0

    def test_fails_when_row_after_prediction(self):
        prediction_ts = datetime(2026, 8, 19, 10, 0, 0, tzinfo=timezone.utc)
        df = self._make_df(datetime(2026, 8, 19, 8, 0, 0, tzinfo=timezone.utc), periods=5, freq="h")
        result = CandleDisciplineChecker.validate(df, prediction_ts)
        assert result.passed is False

    def test_raises_when_raise_on_violation_set(self):
        prediction_ts = datetime(2026, 8, 19, 10, 0, 0, tzinfo=timezone.utc)
        df = self._make_df(datetime(2026, 8, 19, 8, 0, 0, tzinfo=timezone.utc), periods=5, freq="h")
        with pytest.raises(CandleDisciplineViolation):
            CandleDisciplineChecker.validate(df, prediction_ts, raise_on_violation=True)

    def test_empty_df_returns_failed(self):
        prediction_ts = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)
        result = CandleDisciplineChecker.validate(pd.DataFrame(), prediction_ts)
        assert result.passed is False

    def test_timestamp_column_accepted(self):
        prediction_ts = datetime(2026, 8, 19, 16, 0, 0, tzinfo=timezone.utc)
        times = pd.date_range(
            start=datetime(2026, 8, 19, 8, 0, 0, tzinfo=timezone.utc),
            periods=8, freq="h", tz="UTC"
        )
        df = pd.DataFrame({
            "timestamp": times,
            "close": range(8),
        })
        result = CandleDisciplineChecker.validate(df, prediction_ts)
        assert result.passed is True

    def test_result_dict_is_complete(self):
        prediction_ts = datetime(2026, 8, 19, 16, 0, 0, tzinfo=timezone.utc)
        df = self._make_df(datetime(2026, 8, 19, 8, 0, 0, tzinfo=timezone.utc), periods=8, freq="h")
        result = CandleDisciplineChecker.validate(df, prediction_ts)
        d = result.to_dict()
        assert "passed" in d
        assert "violating_rows" in d
        assert "prediction_timestamp" in d
