from typing import Any


class RiskRewardAnalyzer:
    def analyze(self, entry_price: float, profit_target: float, stop_loss: float, probability: float) -> dict[str, Any]:
        """
        Calculate Risk, Reward, RR Ratio, Expected Value.
        """
        if not entry_price or not profit_target or not stop_loss:
            return {}

        reward = abs(profit_target - entry_price)
        risk = abs(entry_price - stop_loss)
        
        rr_ratio = reward / risk if risk > 0 else 0
        
        # Expected value formula: (Probability of Win * Reward) - (Probability of Loss * Risk)
        # Using the model's confidence as probability stub
        prob_win = probability if probability else 0.5
        prob_loss = 1 - prob_win
        
        expected_value = (prob_win * reward) - (prob_loss * risk)
        
        max_drawdown_estimate = risk * 1.5 # Stub calculation
        
        return {
            "risk": round(risk, 4),
            "reward": round(reward, 4),
            "rr_ratio": round(rr_ratio, 2),
            "expected_value": round(expected_value, 4),
            "max_drawdown_estimate": round(max_drawdown_estimate, 4),
            "probability_of_success": prob_win
        }

risk_reward_analyzer = RiskRewardAnalyzer()
