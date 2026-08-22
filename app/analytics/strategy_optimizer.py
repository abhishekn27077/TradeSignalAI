from typing import Any


class StrategyOptimizer:
    @staticmethod
    def generate_recommendations(strategy_stats: dict[str, Any], regime_stats: dict[str, Any]) -> dict[str, Any]:
        """
        Takes Phase 1 and Phase 2 statistics and recommends optimizations.
        """
        recommendations = []
        
        # Strategy level optimizations
        for strat, stats in strategy_stats.items():
            win_rate = stats.get("win_rate", 0)
            if win_rate < 45.0:
                recommendations.append(f"Disable {strat} due to poor win rate ({win_rate}%).")
            elif win_rate > 55.0:
                recommendations.append(f"Increase weight/leverage for {strat} (Strong {win_rate}% win rate).")
                
            profit_factor = stats.get("profit_factor", 1.0)
            if profit_factor > 1.5:
                recommendations.append(f"High Profit Factor on {strat} ({profit_factor:.2f}). Expand position sizing.")
                
        # Regime level optimizations
        for regime, stats in regime_stats.items():
            win_rate = stats.get("win_rate", 0)
            if win_rate < 40.0:
                recommendations.append(f"Tighten stop-loss during {regime} regimes (Win Rate: {win_rate}%).")
            elif win_rate > 55.0:
                recommendations.append(f"Increase take-profit targets during {regime} regimes.")
                
        return {
            "actionable_insights": recommendations,
            "recommended_stop_loss_adj": "-0.5%" if any("Tighten" in r for r in recommendations) else "Keep current",
            "recommended_take_profit_adj": "+1.0%" if any("Increase take-profit" in r for r in recommendations) else "Keep current"
        }
