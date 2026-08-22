from typing import Any


class RiskScoreCalculator:
    """Fuses multiple dimensions into a standardized 0-100 risk score."""
    
    def calculate_risk_score(self, account_state: dict[str, Any], trade_proposal: dict[str, Any]) -> int:
        """
        Calculates a risk score from 0 (Safe) to 100 (Extremely Risky).
        """
        score = 0
        
        # 1. Volatility Penalty (0-30 points)
        volatility = trade_proposal.get("volatility_percentile", 0.5) # 0 to 1.0
        score += int(volatility * 30)
        
        # 2. Drawdown Penalty (0-30 points)
        current_dd = account_state.get("max_drawdown", 0.0)
        # If we are in a 10% drawdown, that adds 20 points
        score += min(30, int(current_dd * 200))
        
        # 3. Leverage Penalty (0-40 points)
        leverage = account_state.get("leverage", 1.0)
        if leverage > 1.0:
            score += min(40, int((leverage - 1.0) * 10))
            
        return min(100, score)

scoring_engine = RiskScoreCalculator()
