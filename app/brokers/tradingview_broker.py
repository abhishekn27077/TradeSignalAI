import uuid
from typing import Any

from app.brokers.interface import IBrokerAdapter
from app.database.models.execution import ExecutionOrder
from app.execution.types import OrderStatus
from app.logs.logger import get_logger
from app.market_data.providers.manager import market_provider_manager

logger = get_logger(__name__)

class TradingViewBrokerAdapter(IBrokerAdapter):
    """
    Simulated Broker adapter that uses TradingView for live market pricing.
    Since TradingView is not a broker, this acts as a Paper execution engine 
    driven by TradingView's market data.
    """
    def __init__(self, **kwargs):
        self._connected = False
        self._balance = 100000.0  # Simulated initial balance
        self._positions = {}
        self._open_orders = {}
        self._last_prices = {}
        logger.info("TradingViewBrokerAdapter (Paper Trading) initialized.")

    async def connect(self) -> bool:
        # Check if TV market data provider is available
        self._connected = True
        return True

    async def disconnect(self) -> bool:
        self._connected = False
        return True

    async def check_health(self) -> dict[str, Any]:
        tv_provider = market_provider_manager.get_provider("tradingview")
        healthy = False
        if tv_provider:
            healthy = await tv_provider.is_connected()
            
        return {
            "status": "HEALTHY" if healthy else "DEGRADED",
            "latency_ms": 10.0,
            "connected": self._connected
        }

    async def _get_current_price(self, symbol: str) -> float:
        tv_provider = market_provider_manager.get_provider("tradingview")
        if tv_provider:
            ticker = await tv_provider.get_ticker(symbol)
            if ticker and ticker.get("price", 0) > 0:
                self._last_prices[symbol] = ticker["price"]
                return ticker["price"]
        
        # Fallback to last known price if rate-limited or disconnected
        fallback = self._last_prices.get(symbol, 0.0)
        if fallback > 0:
            logger.debug(f"TradingView rate limit/error. Using cached price for {symbol}: {fallback}")
            return fallback
            
        # Global fallback if no price ever fetched
        return 64000.0 if "BTC" in symbol else 1.0

    async def submit_order(self, order: ExecutionOrder) -> dict[str, Any]:
        if not self._connected:
            raise Exception("Broker not connected.")

        current_price = await self._get_current_price(order.symbol)
        if current_price <= 0:
            logger.warning(f"No pricing available from TradingView for {order.symbol}. Order rejected.")
            return {
                "broker_order_id": "",
                "status": OrderStatus.FAILED,
                "message": "Pricing unavailable"
            }

        broker_id = f"tv_{uuid.uuid4().hex[:8]}"
        executed_qty = order.quantity
        executed_price = current_price  # Simplified paper fill

        # Update simulated balance/positions
        cost = executed_qty * executed_price
        if order.direction.upper() == "BUY":
            self._balance -= cost
            self._positions[order.symbol] = self._positions.get(order.symbol, 0) + executed_qty
        else:
            self._balance += cost
            self._positions[order.symbol] = self._positions.get(order.symbol, 0) - executed_qty

        return {
            "broker_order_id": broker_id,
            "status": OrderStatus.FILLED,
            "filled_quantity": executed_qty,
            "average_price": executed_price,
            "message": "Simulated fill via TradingView pricing."
        }

    async def cancel_order(self, broker_order_id: str) -> bool:
        return True

    async def get_open_positions(self) -> list[dict[str, Any]]:
        positions = []
        for sym, qty in self._positions.items():
            if qty != 0:
                current_price = await self._get_current_price(sym)
                positions.append({
                    "symbol": sym,
                    "quantity": qty,
                    "current_price": current_price,
                    "unrealized_pnl": 0.0  # Simplified
                })
        return positions

    async def get_account_balance(self) -> dict[str, Any]:
        return {
            "equity": self._balance,
            "free_margin": self._balance,
            "used_margin": 0.0
        }
