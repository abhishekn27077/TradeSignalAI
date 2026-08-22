import logging
import uuid
from typing import Any

from app.database.models.execution import ExecutionOrder
from app.execution.router import smart_router
from app.utils.event_bus import event_bus

logger = logging.getLogger(__name__)

class ExecutionManager:
    """Central gateway for live execution. Converts approved signals into broker orders."""
    
    def __init__(self):
        self.active_orders: dict[str, ExecutionOrder] = {}
        # Subscribe to Risk layer
        event_bus.subscribe("RiskApproved", self.on_risk_approved)
        
    async def on_risk_approved(self, event_data: dict[str, Any]):
        """Triggered when the Risk Engine approves a trade."""
        trade_proposal = event_data.get("trade_proposal", {})
        
        logger.info(f"Execution Manager received approved trade: {trade_proposal}")
        await self.execute_trade(trade_proposal)

    async def execute_trade(self, trade_proposal: dict[str, Any]) -> ExecutionOrder | None:
        """Routes and submits a trade to the appropriate broker."""
        
        symbol = trade_proposal.get("symbol")
        
        # 1. Route to best broker
        adapter = smart_router.get_broker_for_asset(symbol)
        if not adapter:
            logger.error(f"No active broker configured for {symbol}")
            return None
            
        # 2. Create internal order state
        order = ExecutionOrder(
            id=str(uuid.uuid4()),
            broker_id=getattr(adapter, "api_key", "dummy_id"),
            symbol=symbol,
            direction=trade_proposal.get("direction", "BUY"),
            order_type=trade_proposal.get("order_type", "MARKET"),
            quantity=trade_proposal.get("quantity", 0.0),
            status="PENDING",
            requested_price=trade_proposal.get("price")
        )
        
        self.active_orders[order.id] = order
        
        # 3. Submit to broker
        try:
            broker_response = await adapter.submit_order(order)
            
            if broker_response.get("status") == "ACCEPTED":
                order.status = "SUBMITTED"
                order.broker_order_id = broker_response.get("broker_order_id")
                await event_bus.publish("OrderSubmitted", {"internal_id": order.id, "broker_id": order.broker_order_id})
                return order
            else:
                order.status = "REJECTED"
                order.error_message = broker_response.get("error", "Unknown rejection")
                await event_bus.publish("OrderRejected", {"internal_id": order.id, "reason": order.error_message})
                return order
                
        except Exception as e:
            logger.exception("Error submitting order to broker")
            order.status = "ERROR"
            order.error_message = str(e)
            return order

execution_manager = ExecutionManager()
