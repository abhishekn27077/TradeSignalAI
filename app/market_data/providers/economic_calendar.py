import requests
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
from abc import ABC, abstractmethod

from app.logs.logger import get_logger

logger = get_logger(__name__)

class EconomicEvent(BaseModel):
    event_id: str
    timestamp_utc: datetime
    currency: str
    title: str
    impact: str  # LOW, MEDIUM, HIGH
    forecast: Optional[str] = None
    previous: Optional[str] = None
    actual: Optional[str] = None
    source: str
    retrieved_at: datetime
    status: str  # UPCOMING, RELEASED

class IEconomicCalendarProvider(ABC):
    @abstractmethod
    def fetch_events(self, start_date: datetime, end_date: datetime) -> List[EconomicEvent]:
        pass

EconomicCalendarProvider = IEconomicCalendarProvider

class ForexFactoryProvider(IEconomicCalendarProvider):
    """
    Genuine implementation using the official Forex Factory JSON feed.
    Source: https://nfs.faireconomy.media/ff_calendar_thisweek.json
    """
    def __init__(self):
        self.url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

    def fetch_events(self, start_date: datetime, end_date: datetime) -> List[EconomicEvent]:
        return self.get_events(start_date, end_date)

    def get_events(self, start_date: datetime, end_date: datetime, currencies: Optional[List[str]] = None) -> List[EconomicEvent]:
        try:
            logger.info(f"Fetching genuine economic events from ForexFactory: {self.url}")
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            events = []
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            
            for item in data:
                # Parse date like: "2024-05-14T08:30:00-04:00"
                try:
                    event_time = datetime.fromisoformat(item.get("date", "").replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
                except Exception as e:
                    logger.warning(f"Failed to parse event date {item.get('date')}: {e}")
                    continue
                    
                if not (start_date <= event_time <= end_date):
                    continue

                impact_map = {
                    "Low": "LOW",
                    "Medium": "MEDIUM",
                    "High": "HIGH",
                    "Non-Economic": "LOW",
                    "Holiday": "LOW"
                }
                
                impact_raw = item.get("impact", "Low")
                impact = impact_map.get(impact_raw, "LOW")
                
                status = "RELEASED" if event_time < now else "UPCOMING"
                
                events.append(EconomicEvent(
                    event_id=item.get("id", f"{item.get('title')}_{event_time.timestamp()}"),
                    timestamp_utc=event_time,
                    currency=item.get("country", ""),
                    title=item.get("title", ""),
                    impact=impact,
                    forecast=item.get("forecast", ""),
                    previous=item.get("previous", ""),
                    actual=item.get("actual", ""),
                    source="ForexFactory",
                    retrieved_at=now,
                    status=status
                ))
            
            logger.info(f"Successfully retrieved {len(events)} real events from ForexFactory.")
            return events

        except Exception as e:
            logger.error(f"Failed to fetch ForexFactory calendar: {e}")
            return []

ForexFactoryCalendar = ForexFactoryProvider

