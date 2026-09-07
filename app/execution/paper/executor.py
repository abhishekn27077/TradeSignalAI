import uuid
from datetime import datetime, timezone

from ..base import BaseExecutor
from ..types import Order, OrderSide, OrderStatus, OrderType, Position
from app.market_data.service import market_service


class PaperExecutor(BaseExecutor):
    """
    A simulated (paper trading) execution broker.
    Maintains balances and positions in memory.
    """

    def __init__(self, initial_balance: float = 100000.0):
        self.balance = initial_balance
        self.orders: dict[str, Order] = {}
        self.positions: dict[str, Position] = {}

    async def submit_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: float | None = None
    ) -> Order:
        # Input validation — reject obviously invalid orders before any state mutation
        import math
        if quantity <= 0 or (isinstance(quantity, float) and (math.isnan(quantity) or math.isinf(quantity))):
            return Order(id=str(uuid.uuid4()), symbol=symbol, side=side, order_type=order_type,
                         quantity=quantity, price=price, status=OrderStatus.REJECTED,
                         timestamp=datetime.now(timezone.utc))
        if price is not None and (math.isnan(price) or math.isinf(price)):
            return Order(id=str(uuid.uuid4()), symbol=symbol, side=side, order_type=order_type,
                         quantity=quantity, price=price, status=OrderStatus.REJECTED,
                         timestamp=datetime.now(timezone.utc))

        order_id = str(uuid.uuid4())

        # For paper trading, we simulate immediate fills for market orders.
        # Use provided price or fetch real-time price if missing.
        
        if price is None:
            try:
                live_price = await market_service.get_latest_price(symbol)
                if live_price:
                    price = live_price
            except Exception:
                pass

        if order_type == OrderType.MARKET and price is None:
            status = OrderStatus.REJECTED
        elif order_type == OrderType.MARKET and price is not None:
            status = OrderStatus.FILLED
            closed_pnl = self._update_position(symbol, side, quantity, price)
            if closed_pnl is not None:
                try:
                    from app.utils.event_bus import event_bus
                    await event_bus.publish("PositionClosed", {
                        "symbol": symbol,
                        "side": side.name,
                        "quantity": quantity,
                        "exit_price": price,
                        "pnl": closed_pnl,
                        "strategy_used": "Manual",
                        "exit_reason": "Order filled"
                    })
                except Exception:
                    pass
        else:
            status = OrderStatus.PENDING # Limit/Stop orders wait for price triggers

        order = Order(
            id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            status=status,
            timestamp=datetime.now(timezone.utc)
        )
        self.orders[order_id] = order
        return order

    def _update_position(self, symbol: str, side: OrderSide, quantity: float, price: float) -> float | None:
        if symbol not in self.positions:
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=0.0,
                average_entry_price=0.0
            )
            
        pos = self.positions[symbol]
        realized_pnl = None
        
        # Simplistic position update logic for long/short
        # ALWAYS deduct the full order cost from balance first.
        # Then adjust for realized PnL when closing/reducing an opposite position.
        if side == OrderSide.BUY:
            self.balance -= quantity * price  # pay for all units bought
            if pos.quantity < 0:
                # Covering a short position
                cover_qty = min(abs(pos.quantity), quantity)
                realized_pnl = (pos.average_entry_price - price) * cover_qty
                self.balance += realized_pnl
                pos.quantity += quantity
                if pos.quantity > 0:
                    # Flipped to long — average entry is the price of the new long portion
                    pos.average_entry_price = price
            else:
                # Adding to long or opening new long
                total_cost = (pos.quantity * pos.average_entry_price) + (quantity * price)
                pos.quantity += quantity
                pos.average_entry_price = total_cost / pos.quantity

        elif side == OrderSide.SELL:
            self.balance += quantity * price  # receive proceeds from all units sold
            if pos.quantity > 0:
                # Selling into a long position
                sell_qty = min(pos.quantity, quantity)
                realized_pnl = (price - pos.average_entry_price) * sell_qty
                self.balance += realized_pnl
                pos.quantity -= quantity
                if pos.quantity < 0:
                    # Flipped to short — new short portion at `price`
                    pos.average_entry_price = price
            else:
                # Adding to short or opening new short
                total_cost = (abs(pos.quantity) * pos.average_entry_price) + (quantity * price)
                pos.quantity -= quantity
                pos.average_entry_price = total_cost / abs(pos.quantity)
                
        return realized_pnl

    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        if order_id in self.orders and self.orders[order_id].status in [OrderStatus.PENDING, OrderStatus.OPEN]:
            self.orders[order_id].status = OrderStatus.CANCELED
            return True
        return False

    async def get_open_orders(self, symbol: str | None = None) -> list[Order]:
        open_statuses = {OrderStatus.PENDING, OrderStatus.OPEN}
        return [
            order for order in self.orders.values()
            if order.status in open_statuses and (symbol is None or order.symbol == symbol)
        ]

    async def get_position(self, symbol: str) -> Position:
        return self.positions.get(
            symbol,
            Position(symbol=symbol, quantity=0.0, average_entry_price=0.0)
        )
