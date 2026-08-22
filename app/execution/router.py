
from app.brokers.interface import IBrokerAdapter


class SmartOrderRouter:
    """Routes trades to specific brokers based on asset or configuration."""
    
    def __init__(self):
        self.active_brokers: dict[str, IBrokerAdapter] = {}
        
    def add_broker(self, name: str, adapter: IBrokerAdapter):
        self.active_brokers[name] = adapter
        
    def get_broker_for_asset(self, symbol: str) -> IBrokerAdapter | None:
        """
        Determines the correct broker for a given symbol.
        In MVP, we just return the first active broker.
        """
        if not self.active_brokers:
            # Fallback to creating a paper executor if none registered
            try:
                from app.paper_trading.account_manager import account_manager
                accounts = list(account_manager.accounts.values())
                if not accounts:
                    # Create one
                    account_manager.create_account(100000.0)
                    accounts = list(account_manager.accounts.values())
                
                # Mock a broker interface around the paper executor
                class DummyBroker(IBrokerAdapter):
                    def __init__(self):
                        from app.execution.paper.executor import PaperExecutor
                        self.executor = PaperExecutor(initial_balance=100000.0)
                        self.max_equity = 100000.0
                        self.max_drawdown = 0.0
                        
                    async def submit_order(self, order):
                        from app.execution.types import OrderSide, OrderType
                        side = OrderSide.BUY if order.direction == "BUY" else OrderSide.SELL
                        # Map order type
                        o_type = OrderType.MARKET
                        if order.order_type == "LIMIT":
                            o_type = OrderType.LIMIT
                        
                        result = await self.executor.submit_order(
                            order.symbol,
                            side,
                            o_type,
                            order.quantity,
                            order.requested_price
                        )
                        return {
                            "status": result.status.name,
                            "average_price": result.price or order.requested_price or 0.0,
                            "broker_order_id": result.id,
                            "message": "Executed by PaperExecutor"
                        }
                    async def get_positions(self):
                        from app.market_data.service import market_data_service
                        positions = []
                        for sym, pos in self.executor.positions.items():
                            if pos.quantity != 0:
                                current_price = pos.average_entry_price
                                try:
                                    live_price = await market_data_service.get_latest_price(sym)
                                    if live_price:
                                        current_price = live_price
                                except Exception:
                                    pass
                                
                                direction = "LONG" if pos.quantity > 0 else "SHORT"
                                pnl = 0.0
                                if direction == "LONG":
                                    pnl = (current_price - pos.average_entry_price) * abs(pos.quantity)
                                else:
                                    pnl = (pos.average_entry_price - current_price) * abs(pos.quantity)
                                
                                positions.append({
                                    "symbol": pos.symbol,
                                    "quantity": pos.quantity,
                                    "entryPrice": pos.average_entry_price,
                                    "currentPrice": current_price,
                                    "pnl": pnl,
                                    "direction": direction
                                })
                        return positions
                    async def get_balance(self):
                        positions = await self.get_positions()
                        floating_pnl = sum(p["pnl"] for p in positions)
                        bal = self.executor.balance
                        equity = bal + floating_pnl
                        
                        if equity > self.max_equity:
                            self.max_equity = equity
                        
                        dd = 0.0
                        if self.max_equity > 0:
                            dd = (self.max_equity - equity) / self.max_equity * 100
                            if dd > self.max_drawdown:
                                self.max_drawdown = dd
                                
                        return {
                            "balance": bal, 
                            "equity": equity, 
                            "margin": 0, 
                            "free_margin": equity,
                            "drawdown": dd,
                            "max_drawdown": self.max_drawdown,
                            "daily_pnl": floating_pnl  # Proxy for daily PnL
                        }
                    async def get_open_orders(self):
                        open_orders = await self.executor.get_open_orders()
                        return [{"id": o.id, "symbol": o.symbol, "side": o.side.name, "quantity": o.quantity, "status": o.status.name} for o in open_orders]
                        
                self.add_broker("default_dummy", DummyBroker())
            except Exception:
                pass
            
        # Return the first available broker
        return next(iter(self.active_brokers.values()), None)

    async def execute_trade(self, symbol: str, direction: str, quantity: float, order_type: str, price: float | None = None) -> dict:
        broker = self.get_broker_for_asset(symbol)
        if not broker:
            return {"status": "FAILED", "reason": "No broker"}
        
        # Construct a proper ExecutionOrder for the IBrokerAdapter interface
        try:
            import uuid

            from app.database.models.execution import ExecutionOrder
            
            order = ExecutionOrder(
                id=str(uuid.uuid4()),
                broker_id="smart_router",
                symbol=symbol,
                direction=direction,
                order_type=order_type,
                quantity=quantity,
                status="PENDING",
                requested_price=price
            )
            
            result = await broker.submit_order(order)
            
            # Normalize the response for callers
            return {
                "status": result.get("status", "UNKNOWN"),
                "symbol": symbol,
                "side": direction,
                "quantity": quantity,
                "fill_price": result.get("average_price", price or 0),
                "broker_order_id": result.get("broker_order_id", ""),
                "message": result.get("message", "")
            }
        except Exception as e:
            return {"status": "ERROR", "reason": str(e)}

    async def get_positions(self) -> list[dict]:
        positions = []
        for broker in self.active_brokers.values():
            if hasattr(broker, "get_positions"):
                try:
                    broker_positions = await broker.get_positions()
                    positions.extend(broker_positions)
                except Exception:
                    pass
            elif hasattr(broker, "positions"):
                # fallback for paper executor
                for pos in getattr(broker, "positions", {}).values():
                    positions.append({"symbol": pos.symbol, "quantity": pos.quantity, "entryPrice": pos.average_entry_price, "currentPrice": pos.average_entry_price, "pnl": 0.0, "direction": "LONG" if pos.quantity > 0 else "SHORT"})
        return positions

    async def get_orders(self) -> list[dict]:
        orders = []
        for broker in self.active_brokers.values():
            if hasattr(broker, "get_open_orders"):
                try:
                    broker_orders = await broker.get_open_orders()
                    if isinstance(broker_orders, list):
                        for o in broker_orders:
                            orders.append({"id": getattr(o, "id", ""), "symbol": getattr(o, "symbol", ""), "side": getattr(o, "side", ""), "quantity": getattr(o, "quantity", 0), "status": getattr(o, "status", "")})
                except Exception:
                    pass
            elif hasattr(broker, "orders"):
                for o in getattr(broker, "orders", {}).values():
                    orders.append({"id": getattr(o, "id", ""), "symbol": getattr(o, "symbol", ""), "side": getattr(o, "side", ""), "quantity": getattr(o, "quantity", 0), "status": getattr(o, "status", "")})
        return orders

    async def get_balance(self) -> dict:
        # Get balance from the first active broker
        for broker in self.active_brokers.values():
            if hasattr(broker, "get_balance"):
                try:
                    return await broker.get_balance()
                except Exception:
                    pass
            elif hasattr(broker, "balance"):
                bal = broker.balance
                return {"balance": bal, "equity": bal, "margin": 0, "free_margin": bal}
        # Fallback to paper trading account_manager if broker doesn't have it
        try:
            from app.paper_trading.account_manager import account_manager
            accounts = list(account_manager.accounts.values())
            if accounts:
                acc = accounts[0]
                return {"balance": acc.balance, "equity": acc.equity, "margin": acc.used_margin, "free_margin": acc.free_margin}
        except Exception:
            pass
        return {"balance": 100000.0, "equity": 100000.0, "margin": 0, "free_margin": 100000.0}

smart_router = SmartOrderRouter()
