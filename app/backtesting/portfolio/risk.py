class RiskSimulation:
    """Simulates portfolio-level risk controls."""
    def __init__(self, max_risk_per_trade_percent: float = 0.02):
        self.max_risk_percent = max_risk_per_trade_percent

    def calculate_position_size(self, current_capital: float, entry_price: float, stop_loss: float) -> float:
        """
        Calculates position size strictly using risk amount.
        Risk Amount = Capital * max_risk_percent
        Risk Per Share = |Entry - StopLoss|
        Shares = Risk Amount / Risk Per Share
        """
        risk_amount = current_capital * self.max_risk_percent
        risk_per_share = abs(entry_price - stop_loss)
        if risk_per_share == 0:
            return 0
            
        return risk_amount / risk_per_share
