import asyncio

from app.logs.logger import get_logger
from app.utils.event_bus import event_bus

logger = get_logger(__name__)

class ReplayEngine:
    """
    Historical Replay Engine for simulating live market ticks from past data.
    """
    def __init__(self):
        self.is_running = False
        self.playback_speed = 1.0
        self._task = None

    def start_replay(self, start_date: str, end_date: str, speed: float = 1.0):
        self.playback_speed = speed
        self.is_running = True
        
        if self._task:
            self._task.cancel()
            
        self._task = asyncio.create_task(self._replay_loop())
        logger.info(f"Replay started at {speed}x")

    def pause_replay(self):
        self.is_running = False
        logger.info("Replay paused")
        
    def resume_replay(self):
        self.is_running = True
        logger.info("Replay resumed")
        
    def set_speed(self, speed: float):
        self.playback_speed = speed
        logger.info(f"Replay speed set to {speed}x")

    async def _replay_loop(self):
        """
        Background loop streaming historical data as fake live ticks.
        """
        try:
            # We fetch 1h rates for BTCUSD as a sample
            from app.market_data.service import market_service
            rates = await market_service.get_rates("BTCUSD", "1h", count=500)
            
            for rate in rates:
                if not self.is_running:
                    # Wait for resume
                    while not self.is_running:
                        await asyncio.sleep(1)
                
                payload = {
                    "symbol": rate["symbol"],
                    "price": rate["close"],
                    "timestamp": rate["timestamp"],
                    "is_replay": True
                }
                
                await event_bus.publish("ReplayTick", payload)
                
                # Sleep inversely proportional to playback speed
                await asyncio.sleep(1.0 / self.playback_speed)
                
            logger.info("Replay completed")
            self.is_running = False
        except Exception as e:
            logger.error(f"Error in replay loop: {e}")
            self.is_running = False

replay_engine = ReplayEngine()
