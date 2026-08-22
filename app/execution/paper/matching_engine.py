import logging

from app.database.models.paper import OrderStatus
from app.execution.paper.order_manager import order_manager
from app.execution.paper.simulator import fill_simulator
from app.utils.event_bus import event_bus

logger = logging.getLogger(__name__)

class MatchingEngine:
    """Passively matches pending orders when market data arrives."""
    
    def __init__(self):
        self._listener_task = None

    def start(self):
        # Register the handler directly
        event_bus.subscribe("MarketDataTick", self._handle_tick)
        
    async def _handle_tick(self, data: dict):
        await self._evaluate_orders(data["symbol"], data["price"])

    async def _evaluate_orders(self, symbol: str, current_price: float):
        pending_orders = await order_manager.get_pending_orders()
        pending = [o for o in pending_orders if o.symbol == symbol]
        
        for order in pending:
            fill = False
            if order.order_type == "MARKET":
                fill = True
            elif order.order_type == "LIMIT":
                if order.side == "BUY" and current_price <= order.requested_price or order.side == "SELL" and current_price >= order.requested_price:
                    fill = True
            elif order.order_type == "STOP":
                if order.side == "BUY" and current_price >= order.requested_price or order.side == "SELL" and current_price <= order.requested_price:
                    fill = True
                    
            if fill:
                sim_res = fill_simulator.simulate_fill(current_price, order.quantity, order.side)
                # Apply fill
                await order_manager.update_status(order.id, OrderStatus.FILLED, sim_res["fill_price"])
                # Note: Portfolio update would happen here by listening to OrderStatusUpdated

matching_engine = MatchingEngine()
