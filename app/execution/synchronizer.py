import asyncio
import logging

from app.execution.router import smart_router
from app.utils.event_bus import event_bus

logger = logging.getLogger(__name__)

class AccountSynchronizer:
    """Background worker to synchronize real broker accounts into internal state."""
    
    def __init__(self, sync_interval_sec: int = 60):
        self.sync_interval_sec = sync_interval_sec
        self._is_running = False
        self._task = None
        
    def start(self):
        if not self._is_running:
            self._is_running = True
            self._task = asyncio.create_task(self._sync_loop())
            
    def stop(self):
        self._is_running = False
        if self._task:
            self._task.cancel()
            
    async def _sync_loop(self):
        while self._is_running:
            try:
                await self.sync_all_accounts()
            except Exception:
                logger.exception("Error in account sync loop")
                
            await asyncio.sleep(self.sync_interval_sec)
            
    async def sync_all_accounts(self):
        for name, adapter in smart_router.active_brokers.items():
            if getattr(adapter, "connected", False):
                try:
                    balance = await adapter.get_account_balance()
                    positions = await adapter.get_open_positions()
                    
                    await event_bus.publish("BrokerAccountSynced", {
                        "broker_name": name,
                        "balance": balance,
                        "positions": positions
                    })
                except Exception as e:
                    logger.error(f"Failed to sync broker {name}: {e!s}")

account_synchronizer = AccountSynchronizer()
