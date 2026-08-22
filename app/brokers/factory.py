
from app.brokers.interface import IBrokerAdapter
from app.logs.logger import get_logger

logger = get_logger(__name__)


class BrokerFactory:
    _adapters = {}

    @classmethod
    def register(cls, name: str, adapter_class):
        cls._adapters[name] = adapter_class
        logger.debug(f"Broker adapter registered: {name}")

    @classmethod
    def create(cls, adapter_type: str, **kwargs) -> IBrokerAdapter | None:
        adapter_class = cls._adapters.get(adapter_type)
        if adapter_class:
            try:
                return adapter_class(**kwargs)
            except Exception as e:
                logger.warning(f"Failed to create {adapter_type} adapter: {e}")
                return None
        logger.warning(f"Unknown broker adapter type '{adapter_type}'")
        return None

try:
    from app.brokers.tradingview_broker import TradingViewBrokerAdapter
    BrokerFactory.register("TradingView", TradingViewBrokerAdapter)
except Exception as e:
    logger.debug(f"TradingView broker adapter not available: {e}")