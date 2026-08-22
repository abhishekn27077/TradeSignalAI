from typing import Any

from app.logs.logger import get_logger
from app.market_data.providers.manager import market_provider_manager

logger = get_logger(__name__)


class MarketDataService:
    async def get_latest_price(self, symbol: str) -> float | None:
        try:
            ticker = await market_provider_manager.get_ticker(symbol)
            if ticker is None:
                return None
            return ticker.get("price") or ticker.get("bid") or ticker.get("ask") or ticker.get("last")
        except Exception as e:
            logger.warning(f"get_latest_price failed for {symbol}: {e}")
            return None

    async def get_ticker(self, symbol: str) -> dict[str, Any] | None:
        try:
            return await market_provider_manager.get_ticker(symbol)
        except Exception as e:
            logger.warning(f"get_ticker failed for {symbol}: {e}")
            return None

    async def get_rates(self, symbol: str, timeframe: str, count: int = 100) -> list[dict[str, Any]]:
        try:
            return await market_provider_manager.get_rates(symbol, timeframe, count)
        except Exception as e:
            logger.warning(f"get_rates failed: {e}")
            return []


market_service = MarketDataService()