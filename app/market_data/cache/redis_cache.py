import logging

from app.market_data.types import Candle, Tick

logger = logging.getLogger(__name__)

class MarketDataCache:
    """
    Abstracts caching of the latest Market Data using an in-memory dictionary.
    In a real production system, this would wrap `redis.asyncio.Redis`.
    """
    def __init__(self):
        # In-memory mock of Redis
        self._cache: dict[str, str] = {}

    async def set_latest_tick(self, tick: Tick):
        """Cache the latest tick for a symbol."""
        key = f"tick:{tick.symbol}"
        # Serialize to JSON (similar to Redis string storage)
        # Using model_dump_json for Pydantic V2
        self._cache[key] = tick.model_dump_json()

    async def get_latest_tick(self, symbol: str) -> Tick | None:
        """Retrieve the latest cached tick for a symbol."""
        key = f"tick:{symbol}"
        data = self._cache.get(key)
        if data:
            return Tick.model_validate_json(data)
        return None

    async def set_latest_candle(self, candle: Candle):
        """Cache the latest candle for a symbol and timeframe."""
        key = f"candle:{candle.symbol}:{candle.timeframe}"
        self._cache[key] = candle.model_dump_json()

    async def get_latest_candle(self, symbol: str, timeframe: str) -> Candle | None:
        """Retrieve the latest cached candle."""
        key = f"candle:{symbol}:{timeframe}"
        data = self._cache.get(key)
        if data:
            return Candle.model_validate_json(data)
        return None

# Global singleton representing the cache layer
market_cache = MarketDataCache()
