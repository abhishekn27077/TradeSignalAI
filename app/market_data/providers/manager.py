"""
app/market_data/providers/manager.py
====================================
Phase 2, 3, 4, 5 & 6: Data-Truth-First Market Data Provider Manager.

Provider Hierarchy:
1. FOREX / METALS / INDEX:
   - Primary: MT5 (Broker feed)
   - Secondary: TradingView (Validation / Reference)
   - Historical: Yahoo Finance
2. CRYPTO:
   - Primary: BINANCE (Native exchange API/WebSocket)
   - Secondary: TradingView (Validation / Reference)
   - Historical: Yahoo Finance
3. SQLITE:
   - Cache / Historical / Forensic Evidence ONLY.
   - NEVER treated as the authoritative live market price.
"""

from typing import Any, Dict, List, Optional
import logging

from app.logs.logger import get_logger
from app.market_data.providers.base import BaseDataProvider

logger = get_logger(__name__)


class MarketDataProviderManager:
    """
    Coordinates data providers following the authoritative Data-Truth-First hierarchy.
    """

    def __init__(self):
        self._providers: dict[str, BaseDataProvider] = {}

    def register(self, name: str, provider: BaseDataProvider):
        self._providers[name] = provider
        logger.info(f"Market data provider registered: {name}")

    async def get_ticker(self, symbol: str, preferred: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves live ticker through the MarketDataGateway.
        Fail-closed: Returns None / unavailable state if primary feed is disconnected.
        NEVER silently falls back to SQLite candles or synthetic prices.
        """
        from app.market_data.market_data_gateway import market_data_gateway
        
        tick = await market_data_gateway.get_live_ticker(symbol)
        if tick and tick.get("price") is not None and tick.get("is_actionable"):
            return tick

        # If a specific preferred provider was explicitly requested, try direct query
        if preferred and preferred in self._providers:
            provider = self._providers[preferred]
            try:
                direct_tick = await provider.get_ticker(symbol)
                if direct_tick:
                    return direct_tick
            except Exception as e:
                logger.debug(f"Direct provider query failed for {preferred}: {e}")

        # Return gateway result (which includes provenance & status: DATA_UNAVAILABLE / MARKET_CLOSED)
        if tick and tick.get("status") in ("DATA_UNAVAILABLE", "STALE", "EXPIRED", "MARKET_CLOSED"):
            return tick

        return None

    async def get_rates(
        self, symbol: str, timeframe: str, count: int = 100, preferred: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves OHLC bars enforcing strict timeframe, venue, and provider isolation.
        """
        from app.market_data.market_data_gateway import market_data_gateway

        # If preferred provider explicitly specified (e.g. for secondary validation check)
        if preferred and preferred in self._providers:
            provider = self._providers[preferred]
            try:
                rates = await provider.get_rates(symbol, timeframe, count)
                if rates:
                    return rates
            except Exception as e:
                logger.debug(f"Preferred provider {preferred} get_rates failed: {e}")

        return await market_data_gateway.get_rates(symbol, timeframe, count)

    def get_provider(self, name: str) -> Optional[BaseDataProvider]:
        return self._providers.get(name)

    @property
    def available_providers(self) -> List[str]:
        return list(self._providers.keys())


market_provider_manager = MarketDataProviderManager()

# 1. Register Primary Forex Provider (MT5)
try:
    from app.market_data.providers.mt5_provider import mt5_provider
    market_provider_manager.register("mt5", mt5_provider)
except Exception as e:
    logger.warning(f"Could not register MT5 provider: {e}")

# 2. Register Primary Crypto Provider (Binance)
try:
    from app.market_data.providers.binance_provider import binance_crypto_provider
    market_provider_manager.register("binance", binance_crypto_provider)
except Exception as e:
    logger.warning(f"Could not register Binance provider: {e}")

# 3. Register Secondary Validation Provider (TradingView)
try:
    from app.market_data.providers.tradingview import TradingViewDataProvider
    tv_provider = TradingViewDataProvider()
    market_provider_manager.register("tradingview", tv_provider)
except Exception as e:
    logger.warning(f"Could not register TradingView provider: {e}")

# 4. Register Historical / Secondary Provider (Yahoo Finance)
try:
    from app.market_data.providers.yfinance_provider import YFinanceDataProvider
    yf_provider = YFinanceDataProvider()
    market_provider_manager.register("yfinance", yf_provider)
except Exception as e:
    logger.warning(f"Could not register YFinance provider: {e}")