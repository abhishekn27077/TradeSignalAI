from app.backtesting.types import PositionSide


class SlippageSimulator:
    """Simulates market slippage based on a static rate or volatility."""
    def __init__(self, slippage_rate: float = 0.0005):
        self.slippage_rate = slippage_rate

    def apply(self, price: float, side: PositionSide) -> float:
        # Slippage worsens the price
        if side == PositionSide.LONG:
            return price * (1 + self.slippage_rate)
        else:
            return price * (1 - self.slippage_rate)

class CommissionEngine:
    """Calculates simulated trading fees."""
    def __init__(self, commission_rate: float = 0.001):
        self.commission_rate = commission_rate

    def calculate(self, price: float, quantity: float) -> float:
        return price * quantity * self.commission_rate
