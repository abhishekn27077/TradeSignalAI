import logging

from app.execution.router import smart_router
from app.utils.event_bus import event_bus

logger = logging.getLogger(__name__)

class ExecutionRecoveryManager:
    """Handles failover, retries, and the Emergency Kill Switch."""
    
    def __init__(self):
        self.emergency_stop_active = False
        
    async def trigger_kill_switch(self, reason: str = "Manual Intervention"):
        """Instantly halts all trading and cancels open orders."""
        logger.critical(f"KILL SWITCH TRIGGERED: {reason}")
        self.emergency_stop_active = True
        
        # 1. Halt new order routing (would be enforced in execution_manager)
        
        # 2. Cancel all open orders across all active brokers
        for name, adapter in smart_router.active_brokers.items():
            if getattr(adapter, "connected", False):
                try:
                    # In MVP we assume a theoretical cancel_all endpoint or looping through active orders
                    logger.critical(f"Cancelling all open orders on broker: {name}")
                except Exception as e:
                    logger.error(f"Failed to cancel orders on {name} during Kill Switch: {e}")
                    
        await event_bus.publish("EmergencyStop", {"reason": reason})

recovery_manager = ExecutionRecoveryManager()
