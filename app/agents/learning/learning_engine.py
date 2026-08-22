from app.logs.logger import get_logger

logger = get_logger(__name__)

class AILearningEngine:
    """
    Phase 10: AI Learning Engine verification & implementation.
    Tracks strategy performance over time and dynamically tweaks weighting
    or confidence scores based on win rate and profit factors.
    """
    def __init__(self):
        self.strategy_performance = {}

    def log_trade_result(self, strategy_name: str, pnl: float, was_winner: bool):
        """
        Feed result of a completed trade back to the learning engine.
        """
        if strategy_name not in self.strategy_performance:
            self.strategy_performance[strategy_name] = {
                "trades": 0,
                "wins": 0,
                "losses": 0,
                "total_pnl": 0.0,
                "win_rate": 0.0
            }
            
        stats = self.strategy_performance[strategy_name]
        stats["trades"] += 1
        stats["total_pnl"] += pnl
        if was_winner:
            stats["wins"] += 1
        else:
            stats["losses"] += 1
            
        stats["win_rate"] = stats["wins"] / stats["trades"]
        logger.debug(f"Learning Engine updated {strategy_name}: WR={stats['win_rate']:.2%}")

    def get_dynamic_weight(self, strategy_name: str) -> float:
        """
        Returns a confidence multiplier based on historical performance.
        Base multiplier is 1.0. 
        If Win Rate > 60%, boost weight. 
        If Win Rate < 40%, reduce weight.
        """
        if strategy_name not in self.strategy_performance:
            return 1.0
            
        stats = self.strategy_performance[strategy_name]
        
        # Need statistical significance (e.g., at least 5 trades)
        if stats["trades"] < 5:
            return 1.0
            
        wr = stats["win_rate"]
        if wr >= 0.70:
            return 1.25  # High confidence boost
        elif wr >= 0.60:
            return 1.10
        elif wr <= 0.30:
            return 0.50  # Severe penalty
        elif wr <= 0.45:
            return 0.80  # Mild penalty
            
        return 1.0

ai_learning_engine = AILearningEngine()
