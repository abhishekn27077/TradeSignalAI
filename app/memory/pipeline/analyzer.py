from typing import Any

from app.database.models.journal import AIReview, TradeRecord


class LearningAnalyzer:
    """Analyzes trade records and AI reviews to determine if a lesson should be generated."""
    
    @staticmethod
    def analyze_trade_review(trade: TradeRecord, review: AIReview) -> dict[str, Any] | None:
        """
        Extracts key learning signals from a trade review.
        Returns a lesson payload if criteria are met, otherwise None.
        """
        if not review:
            return None
            
        # Example criteria: A high confidence review with a notable mistake or improvement suggestion
        if review.confidence_evaluation >= 0.7:
            if review.mistakes and review.mistakes.lower() != "none" and review.mistakes.lower() != "none.":
                return {
                    "type": "MISTAKE",
                    "trade_id": trade.id,
                    "symbol": trade.symbol,
                    "pnl": trade.pnl,
                    "strategy": trade.strategy_used,
                    "insight": review.mistakes,
                    "actionable": review.improvement_suggestions
                }
            elif review.correct_decisions and trade.pnl > 0:
                return {
                    "type": "SUCCESS",
                    "trade_id": trade.id,
                    "symbol": trade.symbol,
                    "pnl": trade.pnl,
                    "strategy": trade.strategy_used,
                    "insight": review.correct_decisions,
                    "actionable": "Continue observing this pattern."
                }
                
        return None

learning_analyzer = LearningAnalyzer()
