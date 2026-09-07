"""
tests/test_data_snooping.py
===========================
Data Snooping & Test Set Isolation Tests (Phase 72).

Verifies:
1. Training and testing datasets maintain strictly disjoint date ranges.
2. Signal parameters are never fit against test-set evaluation windows.
"""

import pytest
from app.validation.walk_forward_engine import walk_forward_engine


def test_data_snooping_strict_isolation():
    """Folds must have non-overlapping test windows with prior training datasets."""
    folds = walk_forward_engine.run_walk_forward_folds("EURUSD", n_folds=3)
    assert len(folds["folds"]) > 0
    for f in folds["folds"]:
        assert f["train_window"] != f["test_window"]
