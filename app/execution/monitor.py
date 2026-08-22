import asyncio
import logging

from app.execution.router import smart_router

logger = logging.getLogger(__name__)

class BrokerHealthMonitor:
    """Continuously pings brokers to check latency and connectivity."""
    
    def __init__(self, ping_interval_sec: int = 10):
        self.ping_interval_sec = ping_interval_sec
        self._is_running = False
        self._task = None
        
    def start(self):
        if not self._is_running:
            self._is_running = True
            self._task = asyncio.create_task(self._monitor_loop())
            
    def stop(self):
        self._is_running = False
        if self._task:
            self._task.cancel()
            
    async def _monitor_loop(self):
        while self._is_running:
            try:
                for name, adapter in smart_router.active_brokers.items():
                    health = await adapter.check_health()
                    if health.get("status") != "CONNECTED":
                        logger.warning(f"Broker {name} is disconnected or failing health check!")
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                
            await asyncio.sleep(self.ping_interval_sec)

health_monitor = BrokerHealthMonitor()
