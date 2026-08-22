import pytest
import pandas as pd
from datetime import datetime, timezone, timedelta

from app.market_data.providers.consensus import ProviderConsensusEngine, ConsensusStatus


def test_provider_consensus_matching_feeds():
    now = datetime.now(timezone.utc)
    ts = [str(now - timedelta(hours=i)) for i in range(10)]

    df_a = pd.DataFrame({'timestamp': ts, 'close': [1.1000]*10, 'volume': [1000]*10})
    df_b = pd.DataFrame({'timestamp': ts, 'close': [1.1002]*10, 'volume': [1020]*10})  # 0.018% diff (well within 0.5% tolerance)

    engine = ProviderConsensusEngine(max_allowed_deviation_pct=0.005)
    report = engine.evaluate_consensus(df_a, df_b, asset="EURUSD")

    assert report.status == ConsensusStatus.PRIMARY
    assert report.is_consensus_healthy is True
    assert report.disagreement_count == 0


def test_provider_consensus_disagreement():
    now = datetime.now(timezone.utc)
    ts = [str(now - timedelta(hours=i)) for i in range(10)]

    df_a = pd.DataFrame({'timestamp': ts, 'close': [1.1000]*10, 'volume': [1000]*10})
    df_b = pd.DataFrame({'timestamp': ts, 'close': [1.1200]*10, 'volume': [1000]*10})  # ~1.8% diff (exceeds 0.5% limit)

    engine = ProviderConsensusEngine(max_allowed_deviation_pct=0.005)
    report = engine.evaluate_consensus(df_a, df_b, asset="EURUSD")

    assert report.status == ConsensusStatus.DISAGREEMENT
    assert report.is_consensus_healthy is False
    assert report.disagreement_count == 10
