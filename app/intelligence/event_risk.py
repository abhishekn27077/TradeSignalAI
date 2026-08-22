import time
from typing import Literal, Optional
from app.intelligence.economic_calendar import economic_calendar
from app.intelligence.asset_impact_engine import asset_impact_engine
from app.logs.logger import get_logger

logger = get_logger(__name__)

class EventRiskEngine:
    """
    Phase 19: Event Risk Engine
    Calculates dynamic event_risk_score blocking trades if critical events are imminent.
    """
    
    def calculate_event_risk(self, asset: str, prediction_timestamp: Optional[float] = None) -> Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        upcoming_events = economic_calendar.get_upcoming_events(within_seconds=86400, prediction_timestamp=prediction_timestamp) # Next 24h
        
        highest_risk = "LOW"
        current_time = prediction_timestamp if prediction_timestamp else time.time()
        
        for event in upcoming_events:
            affected_assets = asset_impact_engine.get_affected_assets(event["event"])
            if asset in affected_assets or ("USD" in asset and event["currency"] == "USD"):
                time_to_event = event["scheduled_time"] - current_time
                importance = event.get("importance", "MEDIUM")
                
                # Logic to escalate risk as event approaches
                if importance == "CRITICAL" or importance == "HIGH": # ForexFactory uses High instead of Critical sometimes
                    if time_to_event < 3600: # 1 hour
                        return "CRITICAL"
                    elif time_to_event < 14400: # 4 hours
                        highest_risk = self.max_risk(highest_risk, "HIGH")
                    else:
                        highest_risk = self.max_risk(highest_risk, "MEDIUM")
                elif importance == "MEDIUM":
                    if time_to_event < 3600:
                        highest_risk = self.max_risk(highest_risk, "HIGH")
                    elif time_to_event < 14400:
                        highest_risk = self.max_risk(highest_risk, "MEDIUM")
                
        return highest_risk

    @staticmethod
    def max_risk(r1: str, r2: str) -> str:
        risk_levels = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        if risk_levels.get(r1, 1) > risk_levels.get(r2, 1):
            return r1
        return r2

event_risk_engine = EventRiskEngine()
