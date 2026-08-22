"""
tests/test_phase38_date_boundaries.py
Phase 38: Rigorous verification of deterministic IST 00:00:00 to 23:59:59 date boundaries.
"""
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from app.api.v1.signals import _get_ist_day_bounds_utc


def test_ist_today_boundary_exact():
    start_utc, end_utc = _get_ist_day_bounds_utc(0)

    # Convert start_utc and end_utc to IST
    start_ist = start_utc.astimezone(ZoneInfo("Asia/Kolkata"))
    end_ist = end_utc.astimezone(ZoneInfo("Asia/Kolkata"))

    # start_ist must be 00:00:00.000000
    assert start_ist.hour == 0
    assert start_ist.minute == 0
    assert start_ist.second == 0
    assert start_ist.microsecond == 0

    # end_ist must be 00:00:00.000000 of the next calendar day in IST
    assert end_ist.hour == 0
    assert end_ist.minute == 0
    assert end_ist.second == 0
    assert end_ist.microsecond == 0
    assert (end_ist - start_ist) == timedelta(days=1)


def test_ist_yesterday_boundary_exact():
    start_utc, end_utc = _get_ist_day_bounds_utc(1)
    today_start_utc, _ = _get_ist_day_bounds_utc(0)

    # Yesterday's end_utc must exactly equal today's start_utc
    assert end_utc == today_start_utc

    start_ist = start_utc.astimezone(ZoneInfo("Asia/Kolkata"))
    assert start_ist.hour == 0
    assert start_ist.minute == 0
    assert start_ist.second == 0
    assert (today_start_utc - start_utc) == timedelta(days=1)
