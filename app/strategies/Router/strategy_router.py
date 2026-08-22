import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.core.market_clock import MarketClockService
from app.strategies.Structure.models import Direction
from app.strategies.Regime.regime_classifier import MarketRegime, RegimeClassifier


class StrategyType(str, Enum):
    TREND_CONTINUATION_SMC = "TREND_CONTINUATION_SMC"
    RANGE_LIQUIDITY_SWEEP = "RANGE_LIQUIDITY_SWEEP"
    BREAKOUT_MOMENTUM = "BREAKOUT_MOMENTUM"
    ICT_KILLZONE_REVERSAL = "ICT_KILLZONE_REVERSAL"
    MEAN_REVERSION = "MEAN_REVERSION"
    NO_TRADE = "NO_TRADE"


@dataclass
class RoutedStrategy:
    asset: str
    timeframe: str
    strategy_type: StrategyType
    recommended_direction: Direction
    confidence: float
    regime: MarketRegime
    priority: int
    rationale: str
    timestamp_utc: datetime
    timestamp_ist: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "timeframe": self.timeframe,
            "strategy_type": self.strategy_type.value if hasattr(self.strategy_type, 'value') else str(self.strategy_type),
            "recommended_direction": self.recommended_direction.value if hasattr(self.recommended_direction, 'value') else str(self.recommended_direction),
            "confidence": float(self.confidence),
            "regime": self.regime.value if hasattr(self.regime, 'value') else str(self.regime),
            "priority": self.priority,
            "rationale": self.rationale,
            "timestamp_utc": self.timestamp_utc.isoformat() if isinstance(self.timestamp_utc, datetime) else str(self.timestamp_utc),
            "timestamp_ist": self.timestamp_ist,
            "details": self.details,
        }


class StrategyRouter:
    """
    Regime-Adaptive Strategy Router.
    Selects the optimal strategy family based on active market regime and quantitative evidence.
    """

    def __init__(self):
        self.regime_classifier = RegimeClassifier()

    def route_strategy(
        self,
        df: pd.DataFrame,
        asset: str = "UNKNOWN",
        timeframe: str = "1H",
        is_killzone: bool = False,
        has_sweep: bool = False,
        has_smt: bool = False,
        confluence_score: float = 50.0
    ) -> RoutedStrategy:
        now_utc = MarketClockService.get_current_utc()
        now_ist = MarketClockService.format_ist(now_utc)

        regime_info = self.regime_classifier.classify_regime(df, asset=asset, timeframe=timeframe)
        regime = regime_info.regime

        direction = Direction.BULLISH if regime_info.trend_direction == "BULLISH" else (
            Direction.BEARISH if regime_info.trend_direction == "BEARISH" else Direction.NEUTRAL
        )

        if confluence_score < 40.0:
            return RoutedStrategy(
                asset=asset,
                timeframe=timeframe,
                strategy_type=StrategyType.NO_TRADE,
                recommended_direction=Direction.NEUTRAL,
                confidence=0.0,
                regime=regime,
                priority=0,
                rationale="Confluence score below minimum threshold (40.0). Capital preservation active.",
                timestamp_utc=now_utc,
                timestamp_ist=now_ist
            )

        # 1. ICT Killzone Reversal Route
        if is_killzone and (has_sweep or has_smt):
            return RoutedStrategy(
                asset=asset,
                timeframe=timeframe,
                strategy_type=StrategyType.ICT_KILLZONE_REVERSAL,
                recommended_direction=direction,
                confidence=0.88,
                regime=regime,
                priority=1,
                rationale=f"Active Killzone with confirmed liquidity sweep/SMT in {regime.value} regime.",
                timestamp_utc=now_utc,
                timestamp_ist=now_ist
            )

        # 2. Strong Trend Route
        if regime in [MarketRegime.STRONG_TREND, MarketRegime.WEAK_TREND]:
            return RoutedStrategy(
                asset=asset,
                timeframe=timeframe,
                strategy_type=StrategyType.TREND_CONTINUATION_SMC,
                recommended_direction=direction,
                confidence=0.85,
                regime=regime,
                priority=2,
                rationale=f"Trend continuation SMC setup aligned with {direction.value} structural order flow.",
                timestamp_utc=now_utc,
                timestamp_ist=now_ist
            )

        # 3. Range / Mean Reversion Route
        if regime in [MarketRegime.RANGE, MarketRegime.LOW_VOLATILITY]:
            strat = StrategyType.RANGE_LIQUIDITY_SWEEP if has_sweep else StrategyType.MEAN_REVERSION
            return RoutedStrategy(
                asset=asset,
                timeframe=timeframe,
                strategy_type=strat,
                recommended_direction=direction,
                confidence=0.80,
                regime=regime,
                priority=3,
                rationale=f"Range-bound mean reversion setup operating within dealing boundaries.",
                timestamp_utc=now_utc,
                timestamp_ist=now_ist
            )

        # 4. Breakout Route
        if regime in [MarketRegime.BREAKOUT, MarketRegime.HIGH_VOLATILITY]:
            return RoutedStrategy(
                asset=asset,
                timeframe=timeframe,
                strategy_type=StrategyType.BREAKOUT_MOMENTUM,
                recommended_direction=direction,
                confidence=0.75,
                regime=regime,
                priority=4,
                rationale="Volatility expansion breakout with structural momentum confirmation.",
                timestamp_utc=now_utc,
                timestamp_ist=now_ist
            )

        return RoutedStrategy(
            asset=asset,
            timeframe=timeframe,
            strategy_type=StrategyType.NO_TRADE,
            recommended_direction=Direction.NEUTRAL,
            confidence=0.5,
            regime=regime,
            priority=0,
            rationale="Regime is uncertain/transitional without clear structural edge.",
            timestamp_utc=now_utc,
            timestamp_ist=now_ist
        )
