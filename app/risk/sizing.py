from typing import Any


class PositionSizingEngine:
    """Calculates position sizes based on various risk models."""
    
    def calculate_size(self, account_state: dict[str, Any], trade_proposal: dict[str, Any], method: str = "fixed_risk") -> float:
        """
        Calculates the required quantity for a trade.
        Returns the quantity (float).
        """
        equity = account_state.get("equity", 0.0)
        entry_price = trade_proposal.get("price", 0.0)
        stop_loss = trade_proposal.get("stop_loss", 0.0)
        
        if entry_price <= 0 or equity <= 0:
            return 0.0
            
        if method == "fixed_risk":
            # Risk 1% of equity per trade by default
            risk_pct = trade_proposal.get("risk_pct", 0.01)
            return self._calc_fixed_risk(equity, risk_pct, entry_price, stop_loss)
            
        elif method == "kelly":
            # Kelly Criterion: f* = W - ((1 - W) / R)
            # W = Win Probability, R = Win/Loss Ratio
            win_prob = trade_proposal.get("win_prob", 0.5)
            reward_risk_ratio = trade_proposal.get("reward_risk_ratio", 1.0)
            return self._calc_kelly(equity, win_prob, reward_risk_ratio, entry_price, stop_loss)
            
        return 0.0

    def _calc_fixed_risk(self, equity: float, risk_pct: float, entry_price: float, stop_loss: float) -> float:
        if stop_loss <= 0 or stop_loss == entry_price:
            return 0.0
            
        risk_amount = equity * risk_pct
        risk_per_share = abs(entry_price - stop_loss)
        
        if risk_per_share == 0:
            return 0.0
            
        quantity = risk_amount / risk_per_share
        return quantity

    def _calc_kelly(self, equity: float, win_prob: float, reward_risk_ratio: float, entry_price: float, stop_loss: float) -> float:
        if reward_risk_ratio <= 0:
            return 0.0
            
        kelly_pct = win_prob - ((1.0 - win_prob) / reward_risk_ratio)
        
        # Use fractional Kelly (e.g. Half-Kelly) for safety
        fractional_kelly = max(0.0, kelly_pct * 0.5)
        
        # Cap max Kelly at 5% of account
        fractional_kelly = min(0.05, fractional_kelly)
        
        return self._calc_fixed_risk(equity, fractional_kelly, entry_price, stop_loss)

sizing_engine = PositionSizingEngine()
