import pytest
from app.strategies.Confluence.confluence_engine import ConfluenceEngine
from app.strategies.Structure.models import Direction
from app.strategies.Regime.regime_classifier import MarketRegime


def test_confluence_engine_and_collinearity():
    engine = ConfluenceEngine()

    structure_data = {"score": 85.0, "bias": "BULLISH"}
    smc_data = {"has_active_ob": True, "has_active_fvg": True, "in_discount": True}
    liquidity_data = {"has_sweep": True, "sweep_confirmed": True}
    session_data = {"is_killzone": True, "asian_swept": True}
    smt_data = {"state": "BULLISH_SMT", "strength": 0.85}

    # 4 collinear technical momentum indicators
    technical_data = {
        "indicator_votes": [
            {"name": "SUPERTREND", "direction": "BULLISH", "strength": 0.9},
            {"name": "UT_BOT", "direction": "BULLISH", "strength": 0.85},
            {"name": "MACD", "direction": "BULLISH", "strength": 0.8},
            {"name": "RSI", "direction": "BULLISH", "strength": 0.75},
        ]
    }

    res = engine.compute_confluence(
        asset="EURUSD",
        timeframe="1H",
        structure_data=structure_data,
        smc_data=smc_data,
        liquidity_data=liquidity_data,
        session_data=session_data,
        smt_data=smt_data,
        technical_data=technical_data,
        regime=MarketRegime.STRONG_TREND
    )

    assert res.total_score >= 65.0
    assert res.direction == Direction.BULLISH
    assert res.is_actionable is True
    assert res.collinearity_penalty_applied >= 0.0
    assert "layer_scores" in res.to_dict()
