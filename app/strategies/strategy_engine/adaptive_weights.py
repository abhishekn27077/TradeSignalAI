from dataclasses import dataclass
from typing import Any


@dataclass
class LearningResult:
    dimension: str
    dimension_value: str
    lifetime_wr: float
    recent_wr: float
    trade_count: int
    recent_count: int
    trend: str
    adjustment_score: float
    confidence: str

class AdaptiveWeightsEngine:
    """
    Stateless algorithm for dynamically adjusting weights based on historical trade outcomes.
    Accepts history from the TradeSignalAI-v3 Memory/Journal layer.
    """
    RECENT_WINDOW = 100
    MIN_TRADES_FOR_ANALYSIS = 10
    MIN_RECENT_TRADES = 5
    MAX_ADJUSTMENT = 0.10
    DECAY_THRESHOLD = -0.08
    IMPROVEMENT_THRESHOLD = 0.08

    def __init__(self):
        pass
        
    def _calculate_wr(self, trades: list[dict[str, Any]]) -> tuple[int, int, float]:
        cnt = len(trades)
        wins = sum(1 for t in trades if t.get('is_win', False))
        wr = round(wins / cnt * 100, 1) if cnt > 0 else 0.0
        return cnt, wins, wr

    def analyze_dimension(self, dimension: str, dimension_value: str, lifetime_trades: list[dict[str, Any]], recent_trades: list[dict[str, Any]]) -> LearningResult:
        """
        Analyzes performance for a given dimension (e.g., strategy_name, pair, market_regime).
        """
        lt_cnt, lt_wins, lt_wr = self._calculate_wr(lifetime_trades)
        recent_cnt, recent_wins, recent_wr = self._calculate_wr(recent_trades)

        if lt_cnt < self.MIN_TRADES_FOR_ANALYSIS or recent_cnt < self.MIN_RECENT_TRADES:
            trend = "INSUFFICIENT_DATA"
            adj = 0.0
            conf = "NONE"
        else:
            diff = (recent_wr - lt_wr) / 100.0  # normalize diff to percentage point scale
            if diff <= self.DECAY_THRESHOLD:
                trend = "DECAYING"
                adj = max(diff, -self.MAX_ADJUSTMENT)
                conf = "HIGH" if abs(diff) >= 0.12 else "MEDIUM"
            elif diff >= self.IMPROVEMENT_THRESHOLD:
                trend = "IMPROVING"
                adj = min(diff, self.MAX_ADJUSTMENT)
                conf = "HIGH" if abs(diff) >= 0.12 else "MEDIUM"
            else:
                trend = "STABLE"
                adj = 0.0
                conf = "HIGH"

        return LearningResult(
            dimension=dimension,
            dimension_value=str(dimension_value).upper(),
            lifetime_wr=lt_wr,
            recent_wr=recent_wr,
            trade_count=lt_cnt,
            recent_count=recent_cnt,
            trend=trend,
            adjustment_score=adj,
            confidence=conf
        )

    def optimize_weights(self, base_weights: dict[str, float], trades_by_strategy: dict[str, dict[str, list[dict[str, Any]]]]) -> dict[str, float]:
        """
        Adjusts strategy weights given their lifetime and recent trades.
        trades_by_strategy: { "StrategyA": {"lifetime": [...], "recent": [...]} }
        """
        new_weights = {}
        for strategy_name, data in trades_by_strategy.items():
            result = self.analyze_dimension("strategy", strategy_name, data.get("lifetime", []), data.get("recent", []))
            base_w = base_weights.get(strategy_name, 1.0)
            
            # Apply adjustment
            adjusted_w = base_w + result.adjustment_score
            new_weights[strategy_name] = max(0.0, min(1.0, adjusted_w)) # bound between 0 and 1
            
        return new_weights


class ConfidenceCalibrator:
    """
    Stateless algorithm to calculate confidence calibration errors.
    """
    def __init__(self):
        self.conf_levels = [
            ("VERY HIGH", 5, 85.0),
            ("HIGH", 4, 70.0),
            ("MEDIUM", 3, 55.0),
            ("LOW", 2, 40.0),
            ("VERY LOW", 1, 25.0),
        ]

    def calibrate(self, trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Calculates error between predicted win rate (by confidence label) and actual win rate.
        trades should contain 'confidence_numeric' and 'is_win'.
        """
        results = []
        for label, numeric, pred_wr in self.conf_levels:
            # Filter trades matching this confidence level
            matching_trades = [t for t in trades if numeric - 0.5 <= t.get("confidence_numeric", 3) < numeric + 0.5]
            
            cnt = len(matching_trades)
            wins = sum(1 for t in matching_trades if t.get('is_win', False))
            actual_wr = round(wins / cnt * 100, 1) if cnt > 0 else 0.0
            
            error = round(actual_wr - pred_wr, 1)
            
            results.append({
                "confidence_label": label,
                "confidence_numeric": numeric,
                "predicted_wr": pred_wr,
                "actual_wr": actual_wr,
                "calibration_error": error,
                "trades": cnt,
            })
            
        return results
