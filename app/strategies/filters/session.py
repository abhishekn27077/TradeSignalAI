from datetime import datetime
from typing import Any

import pytz


class SessionFilter:
    """
    Detects current trading session (Asian, London, NY, London-NY Overlap).
    """
    def __init__(self):
        self.timezone = pytz.UTC

    def get_session(self, current_time: datetime) -> dict[str, Any]:
        """
        Returns the current session based on UTC time.
        Asian: 00:00 - 08:00 UTC
        London: 08:00 - 16:00 UTC
        NY: 13:00 - 21:00 UTC
        """
        hour = current_time.hour
        
        is_asian = 0 <= hour < 8
        is_london = 8 <= hour < 16
        is_ny = 13 <= hour < 21
        is_overlap = is_london and is_ny
        
        active_session = "CLOSED"
        if is_overlap:
            active_session = "OVERLAP"
        elif is_ny:
            active_session = "NEW_YORK"
        elif is_london:
            active_session = "LONDON"
        elif is_asian:
            active_session = "ASIAN"
            
        return {
            "session": active_session,
            "is_asian": is_asian,
            "is_london": is_london,
            "is_ny": is_ny,
            "is_overlap": is_overlap
        }

session_filter = SessionFilter()
