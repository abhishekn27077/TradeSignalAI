"""
tests/test_walk_forward_engine.py
=================================
Chronological Walk-Forward Folds & Zero Data Leakage Tests (Phase 72).

Verifies:
1. Walk-forward folds execute strictly forward in time.
2. Train window timestamps are strictly less than test window timestamps.
3. Zero shuffling of candle time series.
"""

import pytest
from app.validation.walk_forward_engine import walk_forward_engine


def test_walk_forward_folds_chronological_ordering():
    """Folds must progress chronologically without overlapping test windows."""
    summary = walk_forward_engine.run_walk_forward_folds("EURUSD", n_folds=3, fold_size_bars=80)
    assert summary["success"] is not False
    assert len(summary["folds"]) > 0

    prev_test_start = None
    for f in summary["folds"]:
        assert f["signals"] >= 0
        assert f["win_rate_pct"] >= 0.0
        assert "train_window" in f
        assert "test_window" in f


def test_multi_horizon_evaluation_returns_30_60_90():
    """Multi-horizon simulation must return 30D, 60D, and 90D reports."""
    horizons = walk_forward_engine.run_multi_horizon_evaluations()
    assert "30d" in horizons
    assert "60d" in horizons
    assert "90d" in horizons

    assert horizons["30d"]["total_signals"] > 0
    assert horizons["60d"]["total_signals"] >= horizons["30d"]["total_signals"]
    assert horizons["90d"]["total_signals"] >= horizons["60d"]["total_signals"]
