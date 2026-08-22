import asyncio
from collections.abc import Callable
from typing import Any

from app.logs.logger import get_logger
from app.market_data.providers.manager import market_provider_manager
from app.utils.event_bus import event_bus

logger = get_logger(__name__)

class RealtimeStreamManager:
    def __init__(self):
        self._handlers: dict[str, list] = {}
        self._polling = False
        self._symbols = {"BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "NAS100", "SPX500"}

    def add_symbol(self, symbol: str):
        self._symbols.add(symbol)

    def on_tick(self, symbol: str, handler: Callable):
        if symbol not in self._handlers:
            self._handlers[symbol] = []
        self._handlers[symbol].append(handler)

    def _notify(self, symbol: str, tick: dict[str, Any]):
        for handler in self._handlers.get(symbol, []):
            try:
                handler(tick)
            except Exception as e:
                logger.debug(f"Tick handler error for {symbol}: {e}")

    async def start_polling(self):
        if self._polling:
            return
        self._polling = True
        logger.info("Market data polling started")
        while self._polling:
            try:
                for symbol in list(self._symbols):
                    try:
                        ticker = await asyncio.wait_for(
                            market_provider_manager.get_ticker(symbol),
                            timeout=15.0
                        )
                        if ticker:
                            self._notify(symbol, ticker)
                            try:
                                await event_bus.publish("MarketDataTick", payload=ticker)
                                await event_bus.publish("TickReceived", payload=ticker)
                            except Exception:
                                pass
                    except asyncio.TimeoutError:
                        logger.warning(f"Timeout getting ticker for {symbol}")
                    except Exception as e:
                        logger.debug(f"Polling error for {symbol}: {e}")
            except Exception as e:
                logger.debug(f"Polling loop error: {e}")
            await asyncio.sleep(60.0)

    def stop_polling(self):
        self._polling = False

stream_manager = RealtimeStreamManager()

async def handle_symbol_changed(payload: dict, **kwargs):
    payload_data = kwargs.get("payload", payload) if kwargs else payload
    symbol = payload_data.get("symbol")
    if symbol:
        stream_manager.add_symbol(symbol)
        
try:
    event_bus.subscribe("SymbolChanged", handle_symbol_changed)
except Exception:
    pass