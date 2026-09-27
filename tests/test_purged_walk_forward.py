"""
tests/test_purged_walk_forward.py
=================================
Test Suite for Purged Walk-Forward Cross-Validation Engine.

Validates:
- Strict purging of train samples with label horizons overlapping the test fold
- Post-test embargo window enforcement
- Zero-leakage assertion verification
- Label concurrency and uniqueness calculation
- CUSUM event-based volatility sampling
"""

import pytest
import numpy as np
import pandas as pd

from app.validation.purged_walk_forward import (
    PurgedWalkForwardValidator,
    SampleLabelWindow,
    ConcurrencyMetrics,
)


class TestPurgedWalkForward:
    """
    Test suite for Marcos López de Prado's Purged CV and Embargo algorithms.
    """

    def test_purging_removes_overlapping_labels(self):
        """
        Verify that training samples with forward label windows (t1) crossing
        into the test set (t0_test) are strictly purged.
        """
        n_bars = 200
        # Create sample label windows covering all bars
        label_windows = []
        for i in range(n_bars):
            # Each sample starts at i, holding period is 15 bars: t1 = min(n_bars - 1, i + 15)
            label_windows.append(SampleLabelWindow(sample_index=i, t0_idx=i, t1_idx=min(n_bars - 1, i + 15)))


        validator = PurgedWalkForwardValidator(
            n_splits=3,
            test_size_bars=30,
            embargo_pct=0.05,
            min_train_bars=50,
        )

        splits = list(validator.split_purged_walk_forward(n_bars, label_windows))
        assert len(splits) > 0

        for fold in splits:
            # Check every train index
            for train_idx in fold.train_indices:
                w = next(w for w in label_windows if w.sample_index == train_idx)
                # Purging assertion: outcome t1 must be strictly before test start
                assert w.t1_idx < fold.t0_test, (
                    f"Leakage in fold {fold.fold_id}: sample {train_idx} has t1={w.t1_idx} "
                    f"which overlaps test start {fold.t0_test}"
                )

            # Check purged indices
            assert len(fold.purged_indices) > 0
            for purged_idx in fold.purged_indices:
                w = next(w for w in label_windows if w.sample_index == purged_idx)
                assert w.t1_idx >= fold.t0_test

            # Automated zero-leakage check
            assert validator.assert_zero_leakage(fold, label_windows) is True

    def test_embargo_quarantines_post_test_bars(self):
        """
        Verify that post-test bars within the embargo window are properly quarantined.
        """
        n_bars = 150
        validator = PurgedWalkForwardValidator(
            n_splits=2,
            test_size_bars=25,
            embargo_pct=0.04,  # 4% of 150 = 6 bars
            min_train_bars=40,
        )
        label_windows = [SampleLabelWindow(i, i, i + 5) for i in range(80)]

        splits = list(validator.split_purged_walk_forward(n_bars, label_windows))
        for fold in splits:
            expected_embargo_len = max(1, int(n_bars * 0.04))
            assert len(fold.embargoed_indices) == expected_embargo_len
            assert fold.embargoed_indices[0] == fold.t1_test

    def test_leakage_assertion_raises_on_contamination(self):
        """
        Verify that assert_zero_leakage raises AssertionError if an overlapping
        sample is deliberately placed in train_indices.
        """
        validator = PurgedWalkForwardValidator()
        label_windows = [
            SampleLabelWindow(0, 0, 10),
            SampleLabelWindow(1, 10, 25),  # t1=25 crosses test start 20
        ]
        from app.validation.purged_walk_forward import FoldSplit

        # Deliberately contaminated fold
        contaminated_fold = FoldSplit(
            fold_id=1,
            train_indices=np.array([0, 1]),
            test_indices=np.array([20, 21, 22]),
            purged_indices=np.array([]),
            embargoed_indices=np.array([]),
            t0_test=20,
            t1_test=30,
        )

        with pytest.raises(AssertionError, match="PURGE FAILURE"):
            validator.assert_zero_leakage(contaminated_fold, label_windows)

    def test_concurrency_and_uniqueness_scoring(self):
        """
        Test concurrency and uniqueness metric calculation.
        """
        validator = PurgedWalkForwardValidator()
        # Three completely overlapping windows: concurrency = 3, uniqueness = 1/3
        label_windows = [
            SampleLabelWindow(0, 10, 20),
            SampleLabelWindow(1, 10, 20),
            SampleLabelWindow(2, 10, 20),
        ]
        metrics = validator.compute_label_concurrency(50, label_windows)

        assert metrics.max_concurrency == 3
        assert pytest.approx(metrics.mean_concurrency, 0.01) == 3.0
        assert pytest.approx(metrics.mean_uniqueness, 0.01) == 1.0 / 3.0

    def test_cusum_filter_event_sampling(self):
        """
        Test CUSUM volatility filter on price series with sharp jumps.
        """
        validator = PurgedWalkForwardValidator()
        # Series with a sudden price spike at index 25
        prices = np.ones(50) * 100.0
        prices[25:35] = 110.0  # +10 point jump

        series = pd.Series(prices)
        events = validator.cusum_filter(series, threshold=5.0)

        assert len(events) >= 1
        # Event should trigger at or immediately after index 25
        assert 25 in events or 26 in events
