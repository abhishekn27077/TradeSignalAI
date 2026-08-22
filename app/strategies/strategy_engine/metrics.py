import logging

logger = logging.getLogger(__name__)

class ConfidenceCalculator:
    """
    Calculates signal confidence based on multiple confluences.
    """
    @staticmethod
    def calculate(indicators_agreed: int, total_indicators: int, is_trend_aligned: bool) -> float:
        base_conf = indicators_agreed / max(total_indicators, 1)
        if is_trend_aligned:
            base_conf *= 1.2
        return min(base_conf, 1.0)
        
class StrategyScoring:
    """
    Maintains historical hit rates and live scores for different strategies.
    Used by the AI Agents to weight the trust of different strategies.
    """
    def __init__(self):
        self.scores: dict[str, float] = {}
        
    def update_score(self, strategy_name: str, trade_result: float):
        """
        trade_result: 1.0 for win, -1.0 for loss, 0 for breakeven
        """
        current = self.scores.get(strategy_name, 0.5) # Default 50%
        # EMA style update
        self.scores[strategy_name] = current * 0.9 + (1 if trade_result > 0 else 0) * 0.1
