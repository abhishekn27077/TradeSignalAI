from typing import Any


class ConfidenceScoreEngine:
    """
    Weighted scoring engine to assign confidence percentages to SMC trades.
    """
    def __init__(self, min_threshold_percentage=60.0):
        self.min_threshold = min_threshold_percentage
        
        # Max scores for each component
        self.weights = {
            "trend": 20,
            "structure": 15,
            "liquidity": 15,
            "bos": 15,
            "choch": 10,
            "order_block": 10,
            "fvg": 10,
            "atr": 5,
            "adx": 5,
            "volume": 5
        }
        self.max_total = sum(self.weights.values()) # 110

    def calculate_score(self, evaluation: dict[str, Any]) -> dict[str, Any]:
        """
        Takes a boolean mapping of what conditions are met and calculates a score.
        """
        score = 0
        breakdown = {}
        
        for key, max_val in self.weights.items():
            if evaluation.get(key, False):
                score += max_val
                breakdown[key] = max_val
            else:
                breakdown[key] = 0
                
        percentage = (score / self.max_total) * 100
        
        category = "WEAK"
        if percentage >= 90:
            category = "VERY STRONG"
        elif percentage >= 75:
            category = "STRONG"
        elif percentage >= 60:
            category = "MEDIUM"
            
        return {
            "total_score": score,
            "percentage": percentage,
            "category": category,
            "breakdown": breakdown,
            "passes_threshold": percentage >= self.min_threshold
        }

confidence_engine = ConfidenceScoreEngine()
