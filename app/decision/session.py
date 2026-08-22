from datetime import datetime, timezone
from typing import Any


class SessionAnalyzer:
    def analyze(self, current_time: datetime = None) -> dict[str, Any]:
        """
        Evaluate current market session.
        For crypto it's 24/7, but volume profiles follow traditional sessions.
        Returns a session quality score.
        """
        if not current_time:
            current_time = datetime.now(timezone.utc)
            
        hour = current_time.hour
        active_session = "Asian"
        if 8 <= hour < 12:
            active_session = "London"
        elif 12 <= hour < 16:
            active_session = "London/NY Overlap"
        elif 16 <= hour < 21:
            active_session = "New York"
            
        # Stub score based on volume activity periods
        score = 0.5
        if active_session == "London/NY Overlap":
            score = 1.0
        elif active_session in ["London", "New York"]:
            score = 0.8
            
        return {
            "active_session": active_session,
            "session_score": score
        }

session_analyzer = SessionAnalyzer()
