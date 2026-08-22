
from app.agents.types import DecisionOutput, Signal


class VotingEngine:
    """
    Evaluates individual agent decisions and calculates an aggregate score.
    Includes conflict resolution by comparing confidence and risk scores.
    """
    
    @staticmethod
    def calculate_consensus(decisions: list[DecisionOutput]) -> tuple[Signal, float]:
        """
        Calculates the weighted average signal and confidence.
        """
        if not decisions:
            return Signal.WAIT, 0.0

        buy_weight = 0.0
        sell_weight = 0.0
        total_confidence = 0.0

        for d in decisions:
            # Weighted by confidence. Risk Managers could have specific negative multipliers if needed.
            weight = d.confidence * (1.0 - d.risk_score) 
            
            if d.signal == Signal.BUY:
                buy_weight += weight
            elif d.signal == Signal.SELL:
                sell_weight += weight
                
            total_confidence += d.confidence

        avg_confidence = total_confidence / len(decisions)

        if buy_weight > sell_weight * 1.5:
            return Signal.BUY, avg_confidence
        elif sell_weight > buy_weight * 1.5:
            return Signal.SELL, avg_confidence
        
        # Conflict or lack of strong conviction
        return Signal.WAIT, avg_confidence
