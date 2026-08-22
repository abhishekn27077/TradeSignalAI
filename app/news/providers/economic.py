from datetime import datetime
from typing import Any

from app.logs.logger import get_logger
from app.news.providers.base import BaseNewsProvider

logger = get_logger(__name__)


class EconomicCalendarProvider(BaseNewsProvider):
    @property
    def name(self) -> str:
        return "economic_calendar"

    def __init__(self):
        self._cache: list[dict[str, Any]] = []

    async def fetch_latest(self, limit: int = 20) -> list[dict[str, Any]]:
        return self._cache[:limit]

    async def search(self, query: str) -> list[dict[str, Any]]:
        q = query.lower()
        return [e for e in self._cache if q in str(e.get("title", "")).lower()]

    async def get_historical(self, start_date: datetime, end_date: datetime) -> list[dict[str, Any]]:
        return self._cache

    async def health_check(self) -> bool:
        return True


economic_calendar = EconomicCalendarProvider()