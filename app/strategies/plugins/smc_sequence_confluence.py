import uuid

import pandas as pd

from app.strategies.indicators.market_structure import market_structure_engine
from app.strategies.indicators.sequence_engine import sequence_engine
from app.strategies.strategy_engine.core import BaseStrategy
from app.strategies.strategy_engine.types import (
    RiskLevel,
    SignalDirection,
    SignalStrength,
    StrategySignal,
    Timeframe,
)


class SMCSequenceConfluenceStrategy(BaseStrategy):
    """
    Combines Smart Money Concepts (Market Structure BOS/CHOCH and Liquidity Sweeps)
    with Multi-Candle Sequence analysis (Exhaustion, Breakouts, Wick Clusters).
    """
    def initialize(self):
        super().initialize()

    def reset(self):
        super().reset()

    def analyze(self, symbol: str, data: pd.DataFrame) -> StrategySignal | None:
        if len(data) < 30:
            return None
            
        # 1. Evaluate Market Structure
        ms_result = market_structure_engine.analyse(data)
        
        # 2. Evaluate Sequence Engine
        seq_result = sequence_engine.analyse(data, market_structure=ms_result)
        
        # Look for powerful confluence between Market Structure and Sequence
        direction = None
        confidence = 0.0
        reasoning = []
        
        if ms_result.recent_bos or ms_result.recent_choch:
            structural_break = ms_result.recent_bos or ms_result.recent_choch
            
            # For a SWING signal, require a much stronger sequence confidence
            if structural_break == seq_result.sequence_direction and seq_result.sequence_confidence >= 75.0:
                direction = SignalDirection.BUY if structural_break == "CALL" else SignalDirection.SELL
                confidence = 0.90
                reasoning.append(f"SWING SETUP: Structural Break ({structural_break}) highly aligned with Sequence Momentum")
        
        # Or look for Liquidity Sweep + Reversal Sequence
        elif ms_result.has_strong_sweep and seq_result.sequence_direction == ms_result.sweep_direction:
            if seq_result.sequence_confidence >= 80.0:
                direction = SignalDirection.BUY if ms_result.sweep_direction == "CALL" else SignalDirection.SELL
                confidence = 0.95
                reasoning.append(f"STRONG SWING: Deep Liquidity Sweep aligned with {seq_result.sequence_direction} Reversal Sequence")
                
        if direction and reasoning:
            return StrategySignal(
                signal_id=str(uuid.uuid4()),
                strategy_name=self.name,
                asset=symbol,
                timeframe=Timeframe.H1,
                direction=direction,
                confidence=confidence,
                strength=SignalStrength.STRONG,
                risk_level=RiskLevel.LOW, # Better risk profile for strong swing setups
                reasoning="; ".join(reasoning) + f" (Patterns: {', '.join(seq_result.patterns_detected)})"
            )
            
        return None
