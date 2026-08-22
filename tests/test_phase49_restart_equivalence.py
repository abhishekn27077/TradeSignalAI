import pytest
from datetime import datetime, timezone, timedelta
from app.core.market_clock import market_clock

@pytest.mark.asyncio
async def test_market_clock_ist_formatting():
    """Verify that IST string formatting adheres to Phase 49 requirements."""
    # Test date: Friday, 21 August 2026 18:00:00 UTC
    dt_utc = datetime(2026, 8, 21, 12, 30, tzinfo=timezone.utc) 
    # 12:30 UTC -> 18:00 IST (+5:30)
    
    formatted = market_clock.format_ist(dt_utc)
    # The output should exactly be "Friday, 21 August 2026 06:00 PM IST"
    assert "Friday" in formatted
    assert "21 August 2026" in formatted
    assert "06:00 PM IST" in formatted

@pytest.mark.asyncio
async def test_market_clock_staleness():
    """Verify data staleness logic."""
    now = market_clock.get_current_utc()
    stale_dt = now - timedelta(hours=2) # 2 hours old
    fresh_dt = now - timedelta(minutes=30) # 30 mins old
    
    # max_age_seconds is 3600 (1 hour)
    assert market_clock.is_data_stale(stale_dt) is True
    assert market_clock.is_data_stale(fresh_dt) is False

@pytest.mark.asyncio
async def test_target_time_expiration():
    """Verify signal expiration logic based on UTC time boundaries."""
    now = market_clock.get_current_utc()
    expired_target = now - timedelta(minutes=5)
    future_target = now + timedelta(minutes=60)
    
    assert market_clock.is_target_time_expired(expired_target) is True
    assert market_clock.is_target_time_expired(future_target) is False
