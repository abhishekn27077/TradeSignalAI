import uuid

from app.analytics.patterns import pattern_detector
from app.database.models.journal import Recommendation, TradeRecord


class RecommendationEngine:
    """Generates actionable recommendations based on patterns."""
    
    @staticmethod
    def generate_recommendations(trades: list[TradeRecord]) -> list[Recommendation]:
        if len(trades) < 10:
            return [] # Need sufficient sample size
            
        patterns = pattern_detector.detect_patterns(trades)
        recommendations = []
        
        worst_asset = patterns.get("worst_asset")
        if worst_asset and worst_asset != "None":
            recommendations.append(Recommendation(
                id=str(uuid.uuid4()),
                category="Asset Selection",
                recommendation_text=f"Avoid trading {worst_asset} as it yields negative net PnL.",
                confidence=0.8,
                action_item="Update Risk filter to block this asset."
            ))
            
        worst_strategy = patterns.get("worst_strategy")
        if worst_strategy and worst_strategy != "None":
            recommendations.append(Recommendation(
                id=str(uuid.uuid4()),
                category="Strategy",
                recommendation_text=f"Strategy {worst_strategy} is underperforming.",
                confidence=0.9,
                action_item="Disable strategy in active agents."
            ))
            
        # Direction bias
        lw = patterns.get("long_win_rate", 0)
        sw = patterns.get("short_win_rate", 0)
        if lw < 0.3 and len([t for t in trades if t.direction == "BUY"]) > 5:
            recommendations.append(Recommendation(
                id=str(uuid.uuid4()),
                category="Bias",
                recommendation_text="Long positions have an unusually low win rate.",
                confidence=0.75,
                action_item="Review market macro bias."
            ))
            
        return recommendations

recommendation_engine = RecommendationEngine()
