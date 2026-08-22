import logging
from typing import Any

from app.execution.manager import execution_manager
from app.utils.event_bus import event_bus

logger = logging.getLogger(__name__)

class LifecycleManager:
    """Tracks Order submitted -> filled -> closed states and publishes events."""
    
    def __init__(self):
        event_bus.subscribe("BrokerOrderFilled", self.on_broker_order_filled)
        
    async def on_broker_order_filled(self, event_data: dict[str, Any]):
        """Triggered when the broker adapter confirms an order is filled."""
        internal_id = event_data.get("internal_order_id")
        fill_price = event_data.get("fill_price")
        
        if internal_id in execution_manager.active_orders:
            order = execution_manager.active_orders[internal_id]
            order.status = "FILLED"
            order.filled_price = fill_price
            
            # Calculate slippage
            if order.requested_price and fill_price:
                # Slippage in absolute terms
                order.slippage = abs(fill_price - order.requested_price)
                
            logger.info(f"Order {internal_id} FILLED at {fill_price}. Slippage: {order.slippage}")
            
            # Inform Portfolio and Journal
            await event_bus.publish("OrderFilled", {
                "order_id": order.id,
                "symbol": order.symbol,
                "direction": order.direction,
                "quantity": order.quantity,
                "fill_price": fill_price
            })

lifecycle_manager = LifecycleManager()
