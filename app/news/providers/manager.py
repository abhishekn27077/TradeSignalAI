from typing import Any

from app.logs.logger import get_logger
from app.news.providers.rss import rss_feed_provider

logger = get_logger(__name__)


class NewsProviderManager:
    def __init__(self):
        self._providers: list[Any] = [rss_feed_provider]
        self._cache: list[dict[str, Any]] = []

    def register(self, provider: Any):
        self._providers.append(provider)

    async def fetch_all(self, limit: int = 50) -> list[dict[str, Any]]:
        results = []
        for provider in self._providers:
            try:
                items = await provider.fetch_latest(limit)
                if items:
                    results.extend(items)
            except Exception as e:
                logger.debug(f"News provider fetch failed: {e}")
        results.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        self._cache = results[:limit]
        return self._cache

    async def fetch_by_symbol(self, symbol: str, limit: int = 20) -> list[dict[str, Any]]:
        results = []
        for provider in self._providers:
            try:
                items = await provider.fetch_by_symbol(symbol, limit)
                if items:
                    results.extend(items)
            except Exception as e:
                logger.debug(f"News provider fetch by symbol failed: {e}")
        return results[:limit]

    def get_cached(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._cache[:limit]


news_provider_manager = NewsProviderManager()