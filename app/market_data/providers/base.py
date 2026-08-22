from abc import ABC, abstractmethod

from ..types import Candle, OrderBook, Tick


class BaseDataProvider(ABC):
    """
    Abstract base class for all market data providers (e.g., Binance, Alpaca, Polygon).
    Defines the standard interface that all providers must implement.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the provider (e.g., 'binance')"""

    @abstractmethod
    async def check_health(self) -> bool:
        """Ping the provider's API to ensure it is healthy."""

    @abstractmethod
    async def get_ticker(self, symbol: str) -> Tick:
        """
        Fetch the latest tick (price) for a symbol.
        """

    @abstractmethod
    async def get_historical_klines(
        self, symbol: str, interval: str, limit: int = 100
    ) -> list[Candle]:
        """
        Fetch historical candlestick data.
        """

    @abstractmethod
    async def get_orderbook(self, symbol: str, depth: int = 10) -> OrderBook:
        """
        Fetch the current order book.
        """
