import uuid

import pandas as pd

from app.strategies.strategy_engine.core import BaseStrategy
from app.strategies.strategy_engine.types import (
    RiskLevel,
    SignalDirection,
    SignalStrength,
    StrategySignal,
    Timeframe,
)


class SimpleMomentumStrategy(BaseStrategy):
    """
    A basic momentum strategy plugin.
    Generates a BUY signal if close > open for the last 3 candles.
    """
    def initialize(self):
        super().initialize()

    def reset(self):
        super().reset()

    def analyze(self, symbol: str, data: pd.DataFrame) -> StrategySignal | None:
        if len(data) < 50:
            return None
            
        # Calculate 50 SMA for trend filter
        sma50 = data['close'].rolling(window=50).mean().iloc[-1]
        
        # Calculate Average Volume
        avg_volume = data['volume'].rolling(window=20).mean().iloc[-1]
        
        last = data.iloc[-1]
        prev = data.iloc[-2]
        prev2 = data.iloc[-3]
        
        # Trend check
        uptrend = last['close'] > sma50
        downtrend = last['close'] < sma50
        
        # 3 consecutive candles in same direction
        three_white_soldiers = (last['close'] > last['open']) and (prev['close'] > prev['open']) and (prev2['close'] > prev2['open'])
        three_black_crows = (last['close'] < last['open']) and (prev['close'] < prev['open']) and (prev2['close'] < prev2['open'])
        
        # Volume spike on latest candle
        volume_spike = last['volume'] > (avg_volume * 1.5)
        
        if three_white_soldiers and uptrend and volume_spike:
            return StrategySignal(
                signal_id=str(uuid.uuid4()),
                strategy_name=self.name,
                asset=symbol,
                timeframe=Timeframe.H1,
                direction=SignalDirection.BUY,
                confidence=0.85,
                strength=SignalStrength.STRONG,
                risk_level=RiskLevel.LOW,
                reasoning="STRONG SWING: 3 Bullish Candles with Volume Surge above 50-SMA (Trend Aligned)"
            )
        elif three_black_crows and downtrend and volume_spike:
            return StrategySignal(
                signal_id=str(uuid.uuid4()),
                strategy_name=self.name,
                asset=symbol,
                timeframe=Timeframe.H1,
                direction=SignalDirection.SELL,
                confidence=0.85,
                strength=SignalStrength.STRONG,
                risk_level=RiskLevel.LOW,
                reasoning="STRONG SWING: 3 Bearish Candles with Volume Surge below 50-SMA (Trend Aligned)"
            )
            
        return None
