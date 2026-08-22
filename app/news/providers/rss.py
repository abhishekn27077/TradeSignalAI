from datetime import datetime, timezone
from typing import Any

from app.logs.logger import get_logger
from app.news.providers.base import BaseNewsProvider

logger = get_logger(__name__)

RSS_FEEDS = [
    {"url": "https://feeds.content.dowjones.io/public/rss/mw_topstories", "name": "marketwatch"},
    {"url": "https://finance.yahoo.com/news/rssindex", "name": "yahoo_finance"},
]


class RSSFeedProvider(BaseNewsProvider):
    @property
    def name(self) -> str:
        return "rss"

    def __init__(self):
        self._cache: list[dict[str, Any]] = []

    async def fetch_latest(self, limit: int = 20) -> list[dict[str, Any]]:
        if not self._cache:
            await self._refresh_cache()
        return self._cache[:limit]

    async def search(self, query: str) -> list[dict[str, Any]]:
        q = query.lower()
        return [
            a for a in self._cache
            if q in str(a.get("title", "")).lower() or q in str(a.get("summary", "")).lower()
        ]

    async def get_historical(self, start_date: datetime, end_date: datetime) -> list[dict[str, Any]]:
        return self._cache

    async def fetch_by_symbol(self, symbol: str, limit: int = 10) -> list[dict[str, Any]]:
        upper = symbol.upper()
        return [
            a for a in self._cache
            if upper in str(a.get("title", "")).upper() or upper in str(a.get("summary", "")).upper()
        ][:limit]

    async def _refresh_cache(self):
        import asyncio
        results = []

        async def fetch_feed(feed_info):
            try:
                import httpx
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(feed_info["url"])
                    if resp.status_code != 200:
                        return
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(resp.text)
                    for item in root.iter("item"):
                        results.append({
                            "title": item.findtext("title", ""),
                            "url": item.findtext("link", ""),
                            "summary": item.findtext("description", ""),
                            "source": feed_info["name"],
                            "published_at": item.findtext("pubDate", ""),
                            "fetched_at": datetime.now(timezone.utc).isoformat(),
                        })
            except Exception as e:
                logger.debug(f"RSS feed error for {feed_info['name']}: {e}")

        tasks = [fetch_feed(f) for f in RSS_FEEDS]
        await asyncio.gather(*tasks, return_exceptions=True)
        self._cache = results

    async def health_check(self) -> bool:
        return True


rss_feed_provider = RSSFeedProvider()