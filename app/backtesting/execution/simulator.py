import uuid
from datetime import datetime

from app.backtesting.execution.conditions import CommissionEngine, SlippageSimulator
from app.backtesting.types import PositionSide, TradeResult


class OrderSimulator:
    """Simulates filling an order against historical candle data."""
    def __init__(self, slippage_simulator: SlippageSimulator, commission_engine: CommissionEngine):
        self.slippage = slippage_simulator
        self.commission = commission_engine

    def fill_order(self, symbol: str, side: PositionSide, requested_price: float, quantity: float, timestamp: datetime) -> dict:
        """Returns the simulated fill details."""
        fill_price = self.slippage.apply(requested_price, side)
        fee = self.commission.calculate(fill_price, quantity)
        
        return {
            "fill_price": fill_price,
            "quantity": quantity,
            "fee": fee,
            "timestamp": timestamp
        }

class TradeTracker:
    """Tracks active positions and converts closed positions to TradeResults."""
    def __init__(self):
        self.active_position = None
        self.completed_trades = []

    def open_position(self, symbol: str, side: PositionSide, price: float, quantity: float, fee: float, timestamp: datetime):
        self.active_position = {
            "id": str(uuid.uuid4()),
            "symbol": symbol,
            "side": side,
            "entry_price": price,
            "quantity": quantity,
            "entry_time": timestamp,
            "total_commission": fee
        }

    def close_position(self, price: float, fee: float, timestamp: datetime, reason: str) -> TradeResult | None:
        if not self.active_position:
            return None
            
        pos = self.active_position
        total_fee = pos["total_commission"] + fee
        
        if pos["side"] == PositionSide.LONG:
            pnl = (price - pos["entry_price"]) * pos["quantity"]
            pnl_percent = (price - pos["entry_price"]) / pos["entry_price"]
        else:
            pnl = (pos["entry_price"] - price) * pos["quantity"]
            pnl_percent = (pos["entry_price"] - price) / pos["entry_price"]
            
        pnl -= total_fee # Deduct commissions
        
        result = TradeResult(
            trade_id=pos["id"],
            symbol=pos["symbol"],
            side=pos["side"],
            entry_time=pos["entry_time"],
            exit_time=timestamp,
            entry_price=pos["entry_price"],
            exit_price=price,
            quantity=pos["quantity"],
            pnl=pnl,
            pnl_percent=pnl_percent,
            commission_paid=total_fee,
            slippage_incurred=0.0, # Handled in fill
            exit_reason=reason
        )
        self.completed_trades.append(result)
        self.active_position = None
        return result
