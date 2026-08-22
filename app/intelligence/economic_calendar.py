from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time
from app.logs.logger import get_logger
from app.market_data.providers.economic_calendar import ForexFactoryProvider, EconomicEvent

logger = get_logger(__name__)

class EconomicCalendar:
    """
    Phase 19: Economic Calendar Engine (Real Data Integration)
    Uses the ForexFactory JSON API to fetch real global economic events.
    Strictly prevents lookahead bias for backtesting.
    """
    def __init__(self):
        self.provider = ForexFactoryProvider()
        self._cache_events: List[EconomicEvent] = []
        self._last_fetch_time = None
        
    def _fetch_if_needed(self):
        now = datetime.utcnow()
        if not self._last_fetch_time or (now - self._last_fetch_time).total_seconds() > 3600:
            # Fetch events for the current week (this is what the FF JSON gives us)
            start_dt = now - timedelta(days=7)
            end_dt = now + timedelta(days=7)
            events = self.provider.fetch_events(start_dt, end_dt)
            if events:
                self._cache_events = events
                self._last_fetch_time = now

    def _convert_to_dict(self, event: EconomicEvent, current_time: datetime) -> Dict[str, Any]:
        # STRICT LOOKAHEAD PREVENTION
        # If the current_time (prediction time) is BEFORE the event timestamp_utc, actual is None.
        actual_val = event.actual if event.timestamp_utc <= current_time else None
        
        return {
            "event_id": event.event_id,
            "event": event.title,
            "country": event.currency,
            "currency": event.currency,
            "scheduled_time": event.timestamp_utc.timestamp(),
            "forecast": event.forecast,
            "previous": event.previous,
            "actual": actual_val,
            "importance": event.impact
        }

    def get_upcoming_events(self, within_seconds: int = 86400, prediction_timestamp: Optional[float] = None) -> List[Dict[str, Any]]:
        self._fetch_if_needed()
        current_time = prediction_timestamp if prediction_timestamp else time.time()
        current_dt = datetime.utcfromtimestamp(current_time)
        
        upcoming = []
        for event in self._cache_events:
            evt_time = event.timestamp_utc.timestamp()
            if evt_time > current_time and (evt_time - current_time) <= within_seconds:
                upcoming.append(self._convert_to_dict(event, current_dt))
        return upcoming

    def get_recent_events(self, within_seconds: int = 86400, prediction_timestamp: Optional[float] = None) -> List[Dict[str, Any]]:
        self._fetch_if_needed()
        current_time = prediction_timestamp if prediction_timestamp else time.time()
        current_dt = datetime.utcfromtimestamp(current_time)
        
        recent = []
        for event in self._cache_events:
            evt_time = event.timestamp_utc.timestamp()
            if evt_time <= current_time and (current_time - evt_time) <= within_seconds:
                recent.append(self._convert_to_dict(event, current_dt))
        return recent

economic_calendar = EconomicCalendar()
