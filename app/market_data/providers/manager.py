from typing import Any

from app.logs.logger import get_logger
from app.market_data.providers.base import BaseDataProvider

logger = get_logger(__name__)


class MarketDataProviderManager:
    def __init__(self):
        self._providers: dict[str, BaseDataProvider] = {}

    def register(self, name: str, provider: BaseDataProvider):
        self._providers[name] = provider
        logger.info(f"Market data provider registered: {name}")

    async def get_ticker(self, symbol: str, preferred: str | None = None) -> dict[str, Any] | None:
        # Fast-path: local SQLite historical candle store
        import os
        import sqlite3
        if os.path.exists("tradesignal.db"):
            try:
                conn = sqlite3.connect("tradesignal.db")
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT close, volume, timestamp
                    FROM historical_candles
                    WHERE symbol = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                    """,
                    (symbol,),
                )
                row = cur.fetchone()
                conn.close()
                if row:
                    price = float(row[0])
                    return {
                        "symbol": symbol,
                        "price": price,
                        "bid": price,
                        "ask": price,
                        "last_price": price,
                        "volume": float(row[1]) if row[1] else 100.0,
                        "timestamp": row[2],
                        "provider": "SQLITE_STORE",
                    }
            except Exception as e:
                logger.debug(f"SQLite ticker query failed for {symbol}: {e}")

        if not self._providers:
            logger.warning("No market data providers registered")
            return None

        targets = [preferred] if preferred else list(self._providers.keys())
        for name in targets:
            provider = self._providers.get(name)
            if provider is None:
                continue
            try:
                ticker = await provider.get_ticker(symbol)
                if ticker is not None:
                    return ticker
            except Exception as e:
                logger.debug(f"Provider {name} get_ticker failed: {e}")
                continue

        logger.warning(f"All providers failed for {symbol}")
        return None

    async def get_rates(
        self, symbol: str, timeframe: str, count: int = 100, preferred: str | None = None
    ) -> list[dict[str, Any]]:
        # Fast-path: local SQLite historical candle store (Phase 48 truth store)
        import os
        import sqlite3
        if os.path.exists("tradesignal.db"):
            try:
                conn = sqlite3.connect("tradesignal.db")
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT open, high, low, close, volume, timestamp
                    FROM historical_candles
                    WHERE symbol = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (symbol, count),
                )
                rows = cur.fetchall()
                conn.close()
                if rows and len(rows) >= 10:
                    candles = []
                    for r in reversed(rows):
                        candles.append({
                            "open": float(r[0]),
                            "high": float(r[1]),
                            "low": float(r[2]),
                            "close": float(r[3]),
                            "volume": float(r[4]) if r[4] else 0.0,
                            "time": r[5],
                            "timestamp": r[5],
                        })
                    return candles
            except Exception as e:
                logger.debug(f"SQLite fast-path query failed for {symbol}: {e}")

        if not self._providers:
            logger.warning("No market data providers registered")
            return []

        targets = [preferred] if preferred else list(self._providers.keys())
        for name in targets:
            provider = self._providers.get(name)
            if provider is None:
                continue
            try:
                rates = await provider.get_rates(symbol, timeframe, count)
                if rates:
                    return rates
            except Exception:
                continue

        logger.warning(f"All providers failed to get rates for {symbol}")
        return []

    def get_provider(self, name: str) -> BaseDataProvider | None:
        return self._providers.get(name)

    @property
    def available_providers(self) -> list[str]:
        return list(self._providers.keys())


market_provider_manager = MarketDataProviderManager()

try:
    from app.market_data.providers.yfinance_provider import YFinanceDataProvider
    yf_provider = YFinanceDataProvider()
    market_provider_manager.register("yfinance", yf_provider)
except Exception as e:
    logger.warning(f"Could not initialize YFinance provider: {e}")

try:
    from app.market_data.providers.tradingview import TradingViewDataProvider
    tv_provider = TradingViewDataProvider()
    market_provider_manager.register("tradingview", tv_provider)
except Exception as e:
    logger.warning(f"Could not initialize TradingView provider: {e}")

if not market_provider_manager.available_providers:
    try:
        from app.market_data.providers.simulated import SimulatedDataProvider
        simulated_provider = SimulatedDataProvider()
        market_provider_manager.register("simulated", simulated_provider)
        logger.info("Registered SimulatedDataProvider as fallback")
    except Exception as sim_e:
        logger.error(f"Failed to initialize SimulatedDataProvider: {sim_e}")