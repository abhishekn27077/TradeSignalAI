import uuid

import pandas as pd

from app.strategies.indicators.otc.currency_strength import currency_strength_engine
from app.strategies.indicators.otc.liquidity_sweep import detect_liquidity_sweeps
from app.strategies.strategy_engine.core import BaseStrategy
from app.strategies.strategy_engine.types import (
    RiskLevel,
    SignalDirection,
    SignalStrength,
    StrategySignal,
    Timeframe,
)


class OTCConfluenceStrategy(BaseStrategy):
    """
    Combines Currency Strength and Liquidity Sweeps to find high-probability OTC/Short-term setups.
    """
    def initialize(self):
        super().initialize()
        # Initialize any required state or cache (currency_strength_engine has simple caching inside)

    def reset(self):
        super().reset()

    def analyze(self, symbol: str, data: pd.DataFrame) -> StrategySignal | None:
        if len(data) < 25:
            return None
            
        # 1. Currency Strength Analysis
        cs_result = currency_strength_engine.compute(data)
        
        # 2. Liquidity Sweep Detection
        # Pass empty dict for predefined zones, it will dynamically find swing high/low in data
        sweep_result = detect_liquidity_sweeps(data, liquidity_zones={})
        
        # Look for Confluence
        if cs_result.bias != "NEUTRAL" and sweep_result.has_strong_sweep:
            # We want the sweep direction to align with the currency strength bias
            # Bias CALL (EUR strong) + Sweep CALL (SSL sweep - price traps sellers and rejects up) -> Strong BUY
            if cs_result.bias == sweep_result.dominant_direction and cs_result.tier == "STRONG":
                direction = SignalDirection.BUY if cs_result.bias == "CALL" else SignalDirection.SELL
                
                confidence = 0.90
                
                return StrategySignal(
                    signal_id=str(uuid.uuid4()),
                    strategy_name=self.name,
                    asset=symbol,
                    timeframe=Timeframe.H1,
                    direction=direction,
                    confidence=confidence,
                    strength=SignalStrength.STRONG,
                    risk_level=RiskLevel.LOW,
                    reasoning=f"STRONG SWING: Extreme Currency Strength ({cs_result.summary}) aligned perfectly with Liquidity Sweep ({sweep_result.sweep_summary})"
                )
                
        return None
