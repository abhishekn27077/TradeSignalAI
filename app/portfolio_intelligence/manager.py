import asyncio

from app.logs.logger import get_logger
from app.portfolio_intelligence.correlation import correlation_engine
from app.portfolio_intelligence.currency_strength import currency_strength_engine
from app.portfolio_intelligence.market_rotation import market_rotation_engine
from app.utils.event_bus import event_bus

logger = get_logger(__name__)

class PortfolioIntelligenceManager:
    def __init__(self):
        self._running = False
        
    async def start(self):
        if self._running:
            return
        self._running = True
        logger.info("Starting Portfolio Intelligence Manager...")
        self._task = asyncio.create_task(self._run_loop())
        
    async def _run_loop(self):
        while self._running:
            try:
                # Run background calculations periodically
                strength = currency_strength_engine.calculate()
                correlations = correlation_engine.calculate()
                rotation = market_rotation_engine.analyze()
                
                # Broadcast updates
                await event_bus.publish("CurrencyStrengthChanges", strength)
                await event_bus.publish("CorrelationUpdates", correlations)
                await event_bus.publish("MarketRotationUpdates", rotation)
                
            except Exception as e:
                logger.error(f"Error in portfolio intelligence loop: {e}")
                
            # Run every 5 minutes (stubbed to 60s for testing)
            await asyncio.sleep(60)
            
    async def stop(self):
        self._running = False
        if hasattr(self, '_task') and self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Stopping Portfolio Intelligence Manager...")

portfolio_intelligence_manager = PortfolioIntelligenceManager()
