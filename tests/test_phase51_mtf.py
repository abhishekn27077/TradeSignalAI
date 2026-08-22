import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from app.strategies.MTF.mtf_engine import MTFEngine, AlignmentState
from app.strategies.Structure.models import Direction


def test_mtf_alignment():
    engine = MTFEngine()
    n = 30
    dates = [datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc) + timedelta(hours=i) for i in range(n)]

    # Bullish trend data for all timeframes
    df = pd.DataFrame({
        'timestamp': dates,
        'open': [100.0 + i * 0.5 for i in range(n)],
        'high': [101.0 + i * 0.5 for i in range(n)],
        'low': [99.5 + i * 0.5 for i in range(n)],
        'close': [100.5 + i * 0.5 for i in range(n)],
        'volume': [1000] * n
    })

    res = engine.evaluate_mtf(df, df, df, asset="EURUSD", htf_tf="1D", mtf_tf="1H", ltf_tf="15M")

    assert res.alignment_state == AlignmentState.FULLY_ALIGNED_BULLISH
    assert res.recommended_direction == Direction.BULLISH
    assert res.alignment_score == 1.0
    assert res.is_counter_trend is False
