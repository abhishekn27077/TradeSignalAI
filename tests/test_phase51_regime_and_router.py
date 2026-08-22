import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from app.strategies.Regime.regime_classifier import RegimeClassifier, MarketRegime
from app.strategies.Router.strategy_router import StrategyRouter, StrategyType
from app.strategies.Structure.models import Direction


def test_regime_classifier_and_router():
    classifier = RegimeClassifier()
    router = StrategyRouter()

    n = 60
    dates = [datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc) + timedelta(hours=i) for i in range(n)]

    # Strong trending data
    df_trend = pd.DataFrame({
        'timestamp': dates,
        'open': [100.0 + i * 1.5 for i in range(n)],
        'high': [101.0 + i * 1.5 for i in range(n)],
        'low': [99.5 + i * 1.5 for i in range(n)],
        'close': [100.8 + i * 1.5 for i in range(n)],
        'volume': [1000] * n
    })

    regime_res = classifier.classify_regime(df_trend, asset="EURUSD", timeframe="1H")
    assert regime_res.regime in [MarketRegime.STRONG_TREND, MarketRegime.WEAK_TREND, MarketRegime.BREAKOUT]

    routed = router.route_strategy(df_trend, asset="EURUSD", timeframe="1H", confluence_score=75.0)
    assert routed.strategy_type == StrategyType.TREND_CONTINUATION_SMC
    assert routed.recommended_direction == Direction.BULLISH
