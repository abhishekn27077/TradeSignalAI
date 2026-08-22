from dataclasses import dataclass, field

from app.logs.logger import get_logger

logger = get_logger(__name__)


@dataclass
class OptimizerRecommendation:
    strategy_name: str = ""
    recommendations: list[str] = field(default_factory=list)
    urgency: str = "LOW"
    reasoning: str = ""

    def to_dict(self) -> dict:
        return {
            "strategy_name": self.strategy_name,
            "recommendations": self.recommendations,
            "urgency": self.urgency,
            "reasoning": self.reasoning,
        }


class StrategyOptimizer:
    def __init__(self):
        self.win_rate_thresholds = {
            "increase": 65,
            "maintain": 45,
            "decrease": 35,
        }
        self.profit_factor_thresholds = {
            "increase": 1.5,
            "maintain": 1.2,
        }

    def analyze(self, analytics: dict, config: dict | None = None) -> OptimizerRecommendation:
        recs = []
        urgency = "LOW"

        name = analytics.get("strategy_name", "Unknown")
        win_rate = analytics.get("win_rate", 0)
        profit_factor = analytics.get("profit_factor", 0)
        sharpe = analytics.get("sharpe_ratio", 0)
        total_trades = analytics.get("total_trades", 0)
        max_dd = analytics.get("max_drawdown_pct", 0)

        if total_trades < 5:
            recs.append("Increase allocation (insufficient data yet)")
            urgency = "LOW"
            return OptimizerRecommendation(
                strategy_name=name,
                recommendations=recs,
                urgency=urgency,
                reasoning="Not enough trades for meaningful optimization",
            )

        if win_rate >= self.win_rate_thresholds["increase"] and profit_factor >= self.profit_factor_thresholds["increase"]:
            recs.append("Increase allocation (strong performance)")
            if win_rate >= 75 and profit_factor >= 2.0:
                recs.append("Consider increasing confidence threshold to filter even higher quality setups")
            urgency = "HIGH"
        elif win_rate < self.win_rate_thresholds["decrease"]:
            recs.append("Decrease allocation (poor win rate)")
            recs.append("Consider disabling or retuning strategy parameters")
            if profit_factor < 1.0:
                recs.append("Disable strategy (negative expectancy)")
            urgency = "HIGH"
        elif win_rate < self.win_rate_thresholds["maintain"]:
            recs.append("Maintain current allocation (below average performance)")
            urgency = "MEDIUM"
        else:
            recs.append("Maintain current allocation")
            urgency = "LOW"

        if sharpe < 0.5 and sharpe > 0:
            recs.append("Adjust confidence threshold - low risk-adjusted returns")
        elif sharpe >= 1.5:
            recs.append("Excellent risk-adjusted returns - consider increasing allocation")

        if max_dd > 15:
            recs.append("Reduce position size - drawdown exceeds 15%")
            urgency = "HIGH"
        elif max_dd > 10:
            recs.append("Monitor drawdown - approaching 10%")
            urgency = "MEDIUM"

        if config:
            current_adx = config.get("adx_threshold", 25)
            if win_rate > 60:
                recs.append(f"ADX threshold at {current_adx} appears appropriate")
            elif win_rate < 40:
                recs.append(f"Consider increasing ADX threshold from {current_adx} to {current_adx + 5}")
            atr_mult = config.get("atr_multiplier", 1.0)
            if max_dd > 10:
                recs.append(f"Consider increasing ATR multiplier from {atr_mult} to {atr_mult + 0.5} for wider stops")

        reasoning = (
            f"Analyzed {name}: {total_trades} trades, "
            f"Win Rate {win_rate:.1f}%, Profit Factor {profit_factor:.2f}, "
            f"Sharpe {sharpe:.2f}, Max DD {max_dd:.1f}%"
        )

        return OptimizerRecommendation(
            strategy_name=name,
            recommendations=recs,
            urgency=urgency,
            reasoning=reasoning,
        )

    def analyze_all(self, all_analytics: list[dict], configs: dict[str, dict] | None = None) -> list[dict]:
        results = []
        for a in all_analytics:
            cfg = (configs or {}).get(a.get("strategy_name", ""))
            result = self.analyze(a, cfg)
            results.append(result.to_dict())
        return results


strategy_optimizer = StrategyOptimizer()
