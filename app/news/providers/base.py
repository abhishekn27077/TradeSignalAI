from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class BaseNewsProvider(ABC):
    """
    Abstract interface for all news and economic calendar sources.
    Every provider (Reuters, Bloomberg, RSS, etc.) must implement this.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def fetch_latest(self) -> list[dict[str, Any]]:
        """Fetch the most recent raw news items."""

    @abstractmethod
    async def search(self, query: str) -> list[dict[str, Any]]:
        """Search for news containing specific keywords."""
        
    @abstractmethod
    async def get_historical(self, start_date: datetime, end_date: datetime) -> list[dict[str, Any]]:
        """Fetch historical news for backtesting purposes."""
