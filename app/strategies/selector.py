from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)

class StrategySelector:
    """
    Phase 6: Strategy Selector
    Routes analysis to specific strategies based on current market regime.
    """
    def __init__(self):
        # Map regimes to specific strategy identifiers
        self.regime_strategy_map = {
            "TRENDING": ["SuperTrendStrategy", "PSARStrategy", "TrendFollowingStrategy"],
            "RANGE": ["MeanReversionStrategy", "OscillatorStrategy"],
            "BREAKOUT": ["SMCBreakoutStrategy", "LiquiditySweepStrategy"],
            "PULLBACK": ["FVGStrategy", "OrderBlockStrategy"],
            "REVERSAL": ["CHoCHStrategy", "CounterTrendStrategy"]
        }

    def select_strategies(self, regime_data: dict[str, Any]) -> list[str]:
        """
        Takes output from MarketRegimeEngine and returns a list of strategy names to use.
        """
        trend = regime_data.get("trend", "UNKNOWN")
        state = regime_data.get("state", "UNKNOWN")
        
        selected = []
        
        # 1. State-based selection (More specific than trend)
        if state == "BREAKOUT":
            selected.extend(self.regime_strategy_map["BREAKOUT"])
        elif state == "PULLBACK":
            selected.extend(self.regime_strategy_map["PULLBACK"])
        elif state in ["REVERSAL_BULLISH", "REVERSAL_BEARISH"]:
            selected.extend(self.regime_strategy_map["REVERSAL"])
            
        # 2. Trend-based selection
        if trend in ["BULLISH", "BEARISH", "STRONG_BULLISH", "STRONG_BEARISH"]:
            selected.extend(self.regime_strategy_map["TRENDING"])
        elif trend == "RANGE":
            selected.extend(self.regime_strategy_map["RANGE"])
            
        # Deduplicate while preserving order
        unique_selected = list(dict.fromkeys(selected))
        
        # Fallback if nothing matched
        if not unique_selected:
            unique_selected = ["DefaultConsensusStrategy"]
            
        logger.debug(f"StrategySelector routed {trend}/{state} to {unique_selected}")
        return unique_selected

strategy_selector = StrategySelector()
