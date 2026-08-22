import pytest
from app.strategies.Ensemble.models import StrategyFamily, StrategyVote
from app.strategies.Ensemble.ensemble_engine import StrategyEnsembleEngine


def test_strategy_ensemble_unanimous_buy():
    engine = StrategyEnsembleEngine(consensus_threshold=0.60)

    votes = [
        StrategyVote(StrategyFamily.MARKET_STRUCTURE, "BUY", 0.85, 0.90, 1.0, ["BOS formed"]),
        StrategyVote(StrategyFamily.SMART_MONEY, "BUY", 0.80, 0.85, 1.0, ["Bullish OB"]),
        StrategyVote(StrategyFamily.LIQUIDITY, "BUY", 0.75, 0.80, 1.0, ["Sell-side sweep"]),
        StrategyVote(StrategyFamily.TREND, "BUY", 0.70, 0.80, 1.0, ["SuperTrend green"]),
        StrategyVote(StrategyFamily.MOMENTUM, "BUY", 0.70, 0.80, 1.0, ["UT Bot buy"]),
        StrategyVote(StrategyFamily.MULTI_TIMEFRAME, "BUY", 0.85, 0.90, 1.0, ["HTF 4H bullish"]),
    ]

    decision = engine.evaluate_ensemble(votes, regime="STRONG_TREND")

    assert decision.direction == "BUY"
    assert decision.ensemble_confidence > 0.60
    assert decision.ensemble_score > 60.0
    assert decision.participating_strategies == 6
    assert decision.collinearity_dampener_applied > 0.0  # Proves cluster dampener was applied!


def test_strategy_ensemble_conflicted_neutral():
    engine = StrategyEnsembleEngine(consensus_threshold=0.60)

    votes = [
        StrategyVote(StrategyFamily.MARKET_STRUCTURE, "BUY", 0.80, 0.85, 1.0, ["Bullish structure"]),
        StrategyVote(StrategyFamily.SMART_MONEY, "BUY", 0.80, 0.85, 1.0, ["OB active"]),
        StrategyVote(StrategyFamily.TREND, "SELL", 0.80, 0.85, 1.0, ["Trend bearish"]),
        StrategyVote(StrategyFamily.MOMENTUM, "SELL", 0.80, 0.85, 1.0, ["UT Bot sell"]),
    ]

    decision = engine.evaluate_ensemble(votes, regime="RANGE")

    # Due to split votes, consensus is not reached
    assert decision.direction == "NEUTRAL"
