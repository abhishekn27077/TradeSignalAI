import logging

logger = logging.getLogger(__name__)

class CapitalManager:
    """Manages virtual capital during a backtest."""
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.equity_curve = []
        
    def adjust_capital(self, pnl: float):
        """Adds realized PnL to current capital."""
        self.current_capital += pnl
        
    def record_equity(self, timestamp):
        """Snapshots equity for the curve."""
        self.equity_curve.append((timestamp, self.current_capital))

class PositionManager:
    """Manages active position sizing."""
    def __init__(self, capital_manager: CapitalManager, leverage: float = 1.0):
        self.capital = capital_manager
        self.leverage = leverage

    def calculate_max_quantity(self, price: float) -> float:
        """Returns max quantity affordable given current capital and leverage."""
        buying_power = self.capital.current_capital * self.leverage
        return buying_power / price if price > 0 else 0
