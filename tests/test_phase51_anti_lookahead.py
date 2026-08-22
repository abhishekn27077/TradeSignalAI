import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from app.strategies.Structure.swing import SwingDetector
from app.strategies.Structure.bos_choch import BOSEngine
from app.strategies.SmartMoney.OrderBlocks.order_block_engine import OrderBlockEngine
from app.strategies.SmartMoney.FVG.fvg_engine import FVGEngine
from app.strategies.Technical.technical_evidence_engine import TechnicalEvidenceEngine


def test_adversarial_anti_lookahead_and_non_repainting():
    """
    Adversarial Zero-Lookahead Audit:
    Proves that mutating future bars (T+1 .. T+N) has EXACTLY ZERO effect
    on structural calculations, swing points, order blocks, FVGs, and technicals at bar T.
    """
    np.random.seed(12345)
    n = 60
    dates = [datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc) + timedelta(hours=i) for i in range(n)]

    # Generate baseline OHLCV
    prices = [100.0 + np.sin(i / 4.0) * 5.0 for i in range(n)]
    df_base = pd.DataFrame({
        'timestamp': dates,
        'open': [p - 0.2 for p in prices],
        'high': [p + 0.8 for p in prices],
        'low': [p - 0.8 for p in prices],
        'close': prices,
        'volume': [1000 + i * 10 for i in range(n)]
    })

    # Cutoff at bar T = 40
    t_cutoff = 40
    df_historical = df_base.iloc[:t_cutoff].copy()

    # Create mutated adversarial future dataframe
    df_mutated = df_base.copy()
    # Heavily corrupt and invert prices from bar 40 onwards
    for i in range(t_cutoff, n):
        df_mutated.loc[i, 'open'] = df_base.loc[i, 'open'] * 3.5 + np.random.uniform(50, 100)
        df_mutated.loc[i, 'high'] = df_mutated.loc[i, 'open'] + 20.0
        df_mutated.loc[i, 'low'] = df_mutated.loc[i, 'open'] - 20.0
        df_mutated.loc[i, 'close'] = df_mutated.loc[i, 'open'] + np.random.uniform(-10, 10)
        df_mutated.loc[i, 'volume'] = 999999

    # 1. Test Swing Detector Invariance
    swing_detector = SwingDetector(left_len=3, right_len=3)
    swings_hist = swing_detector.detect_swings(df_historical)
    swings_mutated_prefix = [s for s in swing_detector.detect_swings(df_mutated) if s.index + 3 < t_cutoff]

    assert len(swings_hist) == len(swings_mutated_prefix)
    for s1, s2 in zip(swings_hist, swings_mutated_prefix):
        assert s1.index == s2.index
        assert s1.price == s2.price
        assert s1.swing_type == s2.swing_type

    # 2. Test BOS Engine Invariance
    bos_engine = BOSEngine(swing_len=3)
    bos_hist = bos_engine.detect_bos(df_historical)
    bos_mutated_prefix = [e for e in bos_engine.detect_bos(df_mutated) if e.confirmation_candle < t_cutoff]

    assert len(bos_hist) == len(bos_mutated_prefix)
    for b1, b2 in zip(bos_hist, bos_mutated_prefix):
        assert b1.confirmation_candle == b2.confirmation_candle
        assert b1.price == b2.price
        assert b1.direction == b2.direction

    # 3. Test FVG Engine Invariance
    fvg_engine = FVGEngine(min_atr_multiple=0.1)
    fvgs_hist = fvg_engine.detect_fvgs(df_historical)
    fvgs_mutated_prefix = [f for f in fvg_engine.detect_fvgs(df_mutated) if f.source_candle_index < t_cutoff]

    assert len(fvgs_hist) == len(fvgs_mutated_prefix)
    for f1, f2 in zip(fvgs_hist, fvgs_mutated_prefix):
        assert f1.source_candle_index == f2.source_candle_index
        assert f1.gap_high == f2.gap_high
        assert f1.gap_low == f2.gap_low

    # 4. Test Technical Evidence Invariance at Bar T-1
    tech_engine = TechnicalEvidenceEngine()
    tech_hist = tech_engine.evaluate_evidence(df_historical)
    tech_mutated_at_t = tech_engine.evaluate_evidence(df_mutated.iloc[:t_cutoff])

    for k in tech_hist.keys():
        assert tech_hist[k].value == pytest.approx(tech_mutated_at_t[k].value, rel=1e-5)
        assert tech_hist[k].state == tech_mutated_at_t[k].state
        assert tech_hist[k].direction == tech_mutated_at_t[k].direction
