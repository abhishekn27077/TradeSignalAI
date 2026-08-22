import uuid
from typing import Any

from app.paper_trading.account_manager import VirtualAccount


class Position:
    def __init__(self, account_id: str, symbol: str, side: str, entry_price: float, quantity: float, strategy: str = "Manual"):
        self.id = str(uuid.uuid4())
        self.account_id = account_id
        self.symbol = symbol
        self.side = side
        self.entry_price = entry_price
        self.quantity = quantity
        self.strategy = strategy
        self.stop_loss = None
        self.take_profit = None
        self.trailing_stop = None

class PortfolioManager:
    """Manages active open positions and evaluates exposure."""
    def __init__(self):
        self.positions: dict[str, Position] = {}

    def add_position(self, account: VirtualAccount, symbol: str, side: str, entry_price: float, quantity: float, strategy: str = "Manual") -> Position:
        # Simplest single position append. Netting/scaling out would go here.
        pos = Position(account.account_id, symbol, side, entry_price, quantity, strategy)
        self.positions[pos.id] = pos
        
        # Fire event for frontend synchronization
        import asyncio

        from app.utils.event_bus import event_bus
        asyncio.create_task(event_bus.publish("PositionOpened", {
            "id": pos.id,
            "account_id": pos.account_id,
            "symbol": pos.symbol,
            "side": pos.side,
            "entry_price": pos.entry_price,
            "quantity": pos.quantity,
            "strategy_used": pos.strategy
        }))
        
        return pos

    async def close_position(self, position_id: str, close_price: float, exit_reason: str = "Manual") -> float:
        """Returns the realized PnL of the closed position and publishes the event."""
        if position_id not in self.positions:
            return 0.0
            
        pos = self.positions.pop(position_id)
        if pos.side == "BUY" or pos.side == "LONG":
            pnl = (close_price - pos.entry_price) * pos.quantity
        else:
            pnl = (pos.entry_price - close_price) * pos.quantity
            
        # Fire event for the Journal
        from app.utils.event_bus import event_bus
        await event_bus.publish("PositionClosed", {
            "account_id": pos.account_id,
            "symbol": pos.symbol,
            "side": pos.side,
            "entry_price": pos.entry_price,
            "exit_price": close_price,
            "quantity": pos.quantity,
            "pnl": pnl,
            "exit_reason": exit_reason,
            "strategy_used": pos.strategy
        })
            
        return pnl

    def get_positions(self, account_id: str = None) -> list[Position]:
        if account_id:
            return [p for p in self.positions.values() if p.account_id == account_id]
        return list(self.positions.values())

    def get_portfolio_snapshot(self, account: VirtualAccount) -> dict[str, Any]:
        """Builds a complete snapshot of the portfolio state including exposure and margin."""
        from app.portfolio.exposure import exposure_manager
        from app.portfolio.margin import margin_manager
        
        # Convert objects to dicts for the exposure manager
        positions_list = []
        for p in self.get_positions(account.account_id):
            positions_list.append({
                "symbol": p.symbol,
                "direction": p.side,
                "quantity": p.quantity,
                "current_price": p.entry_price # MVP approximation until live pricing is hooked up
            })
            
        exposure = exposure_manager.calculate_exposure(positions_list)
        gross_exposure = exposure["gross_exposure"]
        leverage = margin_manager.calculate_leverage(account.equity, gross_exposure)
        
        return {
            "account_id": account.account_id,
            "equity": account.equity,
            "cash": account.balance,
            "positions": positions_list,
            "gross_exposure": gross_exposure,
            "net_exposure": exposure["net_exposure"],
            "margin_used": account.used_margin,
            "leverage": leverage,
            "margin_called": margin_manager.check_margin_call(account.equity, gross_exposure)
        }

    async def _on_trade_executed(self, payload: dict, **kwargs):
        payload_data = kwargs.get("payload", payload) if kwargs else payload
        result = payload_data.get("result", {})
        if result.get("status") in ["SUCCESS", "FILLED"]:
            # Need an account
            from app.paper_trading.account_manager import account_manager
            accounts = list(account_manager.accounts.values())
            if not accounts:
                account = account_manager.create_account()
            else:
                account = accounts[0]
            
            self.add_position(
                account=account,
                symbol=result.get("symbol", payload_data.get("symbol", "UNKNOWN")),
                side=result.get("side", "BUY"),
                entry_price=result.get("fill_price", 0.0),
                quantity=result.get("quantity", 0.0),
                strategy=payload_data.get("strategy_used", "Manual")
            )

portfolio_manager = PortfolioManager()

try:
    from app.utils.event_bus import event_bus
    event_bus.subscribe("trade_executed", portfolio_manager._on_trade_executed)
except Exception:
    pass
