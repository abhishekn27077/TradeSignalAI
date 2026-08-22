import random


class SlippageEngine:
    """Calculates live slippage."""
    def __init__(self, base_slippage: float = 0.0001):
        self.base = base_slippage

    def apply(self, price: float, side: str, volatility_factor: float = 1.0) -> float:
        # Randomize slippage slightly to simulate real conditions
        variable_slip = self.base * volatility_factor * random.uniform(0.5, 1.5)
        if side == "BUY":
            return price * (1 + variable_slip)
        return price * (1 - variable_slip)

class SpreadEngine:
    """Simulates bid/ask spread."""
    def __init__(self, spread_pct: float = 0.0002):
        self.spread_pct = spread_pct

    def get_bid_ask(self, mark_price: float):
        half_spread = mark_price * (self.spread_pct / 2.0)
        return mark_price - half_spread, mark_price + half_spread

class CommissionEngine:
    """Calculates commissions for paper trades."""
    def __init__(self, rate: float = 0.001):
        self.rate = rate

    def calculate(self, executed_price: float, quantity: float) -> float:
        return executed_price * quantity * self.rate

class FillSimulator:
    """Combines spread, slippage, and commissions for a final fill."""
    def __init__(self):
        self.slippage = SlippageEngine()
        self.spread = SpreadEngine()
        self.commission = CommissionEngine()

    def simulate_fill(self, mark_price: float, quantity: float, side: str, volatility: float = 1.0) -> dict:
        bid, ask = self.spread.get_bid_ask(mark_price)
        base_price = ask if side == "BUY" else bid
        
        filled_price = self.slippage.apply(base_price, side, volatility)
        fee = self.commission.calculate(filled_price, quantity)
        
        return {
            "fill_price": filled_price,
            "fee": fee
        }

fill_simulator = FillSimulator()
