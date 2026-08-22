from app.logs.logger import get_logger
from app.market_data.historical.manager import historical_data_manager
from app.utils.event_bus import event_bus

logger = get_logger(__name__)


class DataReplayManager:
    async def start_replay(self, config, interval: str = "1m"):
        logger.info(f"Starting replay for {config.symbol}")
        try:
            candles = await historical_data_manager.get_rates(config.symbol, interval, 100)
            for candle in candles:
                try:
                    await event_bus.publish("CandleClosed", payload=candle)
                except Exception:
                    pass
            logger.info(f"Replay finished for {config.symbol}")
        except Exception as e:
            logger.warning(f"Replay error: {e}")


replay_manager = DataReplayManager()