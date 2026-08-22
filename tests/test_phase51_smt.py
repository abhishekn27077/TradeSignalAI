import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from app.strategies.Correlation.smt_engine import (
    SMTDivergenceDetector, SMTResult, SMTState
)
from app.strategies.Structure.models import Direction


def test_smt_divergence():
    detector = SMTDivergenceDetector(swing_len=2)
    n = 30
    dates = [datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc) + timedelta(hours=i) for i in range(n)]

    # Pair A (EURUSD): Makes Lower Low (Low at bar 5 = 1.0800, Low at bar 15 = 1.0750)
    df_a = pd.DataFrame({
        'timestamp': dates,
        'open': [1.0850] * n,
        'high': [1.0900] * n,
        'low': [1.0820] * n,
        'close': [1.0850] * n,
    })
    df_a.loc[5, 'low'] = 1.0800
    df_a.loc[15, 'low'] = 1.0750

    # Inversely Correlated Pair B (DXY): Fails to make Higher High (High at bar 5 = 104.0, High at bar 15 = 103.5 -> Lower High)
    df_b = pd.DataFrame({
        'timestamp': dates,
        'open': [102.5] * n,
        'high': [103.0] * n,
        'low': [102.0] * n,
        'close': [102.5] * n,
    })
    df_b.loc[5, 'high'] = 104.0
    df_b.loc[15, 'high'] = 103.5

    res = detector.detect_smt(df_a, df_b, asset_a="EURUSD", asset_b="DXY", timeframe="1H")

    assert res.state == SMTState.BULLISH_SMT
    assert res.direction == Direction.BULLISH
    assert res.strength >= 0.8
