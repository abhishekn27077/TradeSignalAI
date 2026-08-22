import pytest
from datetime import datetime, timezone

from app.strategies.Explanation.explanation_engine import SignalExplanationEngine
from app.strategies.Confluence.confluence_engine import ConfluenceScore
from app.strategies.Router.strategy_router import RoutedStrategy, StrategyType
from app.strategies.Structure.models import Direction
from app.strategies.Regime.regime_classifier import MarketRegime


def test_signal_explanation_tree():
    engine = SignalExplanationEngine()
    now_utc = datetime.now(timezone.utc)

    confluence = ConfluenceScore(
        asset="EURUSD",
        timeframe="1H",
        total_score=82.5,
        direction=Direction.BULLISH,
        confidence=0.83,
        is_actionable=True,
        structure_score=24.0,
        smc_score=18.0,
        liquidity_score=12.0,
        session_score=8.0,
        smt_score=7.5,
        technical_score=13.0,
        collinearity_penalty_applied=1.2,
        regime="STRONG_TREND",
        timestamp_utc=now_utc,
        timestamp_ist="Saturday, 22 August 2026 06:30 PM IST"
    )

    strategy = RoutedStrategy(
        asset="EURUSD",
        timeframe="1H",
        strategy_type=StrategyType.TREND_CONTINUATION_SMC,
        recommended_direction=Direction.BULLISH,
        confidence=0.85,
        regime=MarketRegime.STRONG_TREND,
        priority=1,
        rationale="Trend continuation setup",
        timestamp_utc=now_utc,
        timestamp_ist="Saturday, 22 August 2026 06:30 PM IST"
    )

    explanation = engine.generate_explanation(
        signal_id="SIG-EURUSD-001",
        asset="EURUSD",
        timeframe="1H",
        confluence=confluence,
        strategy=strategy,
        entry_price=1.0850,
        stop_loss=1.0800,
        take_profit=1.0950
    )

    assert len(explanation.why_evidence) > 0
    assert len(explanation.risk_factors) > 0
    assert len(explanation.invalidation_triggers) > 0
    assert "Risk-to-Reward" in explanation.risk_factors[0]
    assert "Stop Loss" in explanation.invalidation_triggers[0]
