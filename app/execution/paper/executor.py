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
        if side == OrderSide.BUY:
            if pos.quantity < 0:
                # Covering a short position
                cover_qty = min(abs(pos.quantity), quantity)
                realized_pnl = (pos.average_entry_price - price) * cover_qty
                
            new_qty = pos.quantity + quantity
            if new_qty > 0 and pos.quantity >= 0:
                # Averaging up/down on a long position
                total_cost = (pos.quantity * pos.average_entry_price) + (quantity * price)
                pos.average_entry_price = total_cost / new_qty
            elif new_qty > 0 and pos.quantity < 0:
                # Flipped from short to long
                pos.average_entry_price = price
                
            pos.quantity = new_qty
            self.balance -= quantity * price
            if realized_pnl is not None:
                self.balance += realized_pnl
                
        elif side == OrderSide.SELL:
            if pos.quantity > 0:
                # Selling a long position
                sell_qty = min(pos.quantity, quantity)
                realized_pnl = (price - pos.average_entry_price) * sell_qty
                
            new_qty = pos.quantity - quantity
            if new_qty < 0 and pos.quantity <= 0:
                # Averaging up/down on a short position
                total_cost = (abs(pos.quantity) * pos.average_entry_price) + (quantity * price)
                pos.average_entry_price = total_cost / abs(new_qty)
            elif new_qty < 0 and pos.quantity > 0:
                # Flipped from long to short
                pos.average_entry_price = price
                
            pos.quantity = new_qty
            self.balance += quantity * price
            if realized_pnl is not None:
                self.balance += realized_pnl
                
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
