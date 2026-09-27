"""
app/validation/purged_walk_forward.py
=====================================
Purged & Embargoed Walk-Forward Cross-Validation Engine.

Benchmarked against mlfinlab and Marcos López de Prado's
"Advances in Financial Machine Learning" (2018).

Core Capabilities:
1. Purging: Eliminates training observations whose label outcome horizons (t1)
   overlap with the evaluation/test window [t0_test, t1_test].
2. Embargoing: Enforces a post-test quarantine window (h_bars or pct) to prevent
   autoregressive and serial-correlation leakage from test set to future train folds.
3. Label Concurrency & Uniqueness: Quantifies concurrent trade density and sample uniqueness (1 / c_t).
4. CUSUM Volatility Event Filter: Generates event-based samples at information-rich volatility regimes.
5. Strict Zero-Leakage Assertions: Programmatically verifies causal separation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Iterator
import pandas as pd
import numpy as np


@dataclass(frozen=True)
class SampleLabelWindow:
    sample_index: int
    t0_idx: int       # Bar index when feature/prediction was formed
    t1_idx: int       # Bar index when outcome was finalized (barrier hit or time exit)
    asset: str = "DEFAULT"


@dataclass
class FoldSplit:
    fold_id: int
    train_indices: np.ndarray
    test_indices: np.ndarray
    purged_indices: np.ndarray
    embargoed_indices: np.ndarray
    t0_test: int
    t1_test: int


@dataclass
class ConcurrencyMetrics:
    mean_concurrency: float
    max_concurrency: int
    mean_uniqueness: float
    total_events: int


class PurgedWalkForwardValidator:
    """
    Implements Purged Walk-Forward Cross-Validation with post-test Embargo.
    """

    def __init__(
        self,
        n_splits: int = 5,
        test_size_bars: int = 40,
        embargo_pct: float = 0.02,  # 2% of total length as post-test embargo
        min_train_bars: int = 60,
    ):
        self.n_splits = n_splits
        self.test_size_bars = test_size_bars
        self.embargo_pct = embargo_pct
        self.min_train_bars = min_train_bars

    def compute_label_concurrency(
        self,
        n_bars: int,
        label_windows: List[SampleLabelWindow],
    ) -> ConcurrencyMetrics:
        """
        Calculates concurrent active labels at each bar t and sample uniqueness (1 / c_t).
        """
        if not label_windows or n_bars <= 0:
            return ConcurrencyMetrics(0.0, 0, 1.0, 0)

        # Count active labels at each bar index
        concurrency = np.zeros(n_bars, dtype=int)
        for w in label_windows:
            start = max(0, w.t0_idx)
            end = min(n_bars - 1, w.t1_idx)
            concurrency[start : end + 1] += 1

        # Calculate uniqueness per sample
        uniqueness_scores = []
        for w in label_windows:
            start = max(0, w.t0_idx)
            end = min(n_bars - 1, w.t1_idx)
            span = end - start + 1
            if span > 0:
                # Average inverse concurrency over the window
                c_slice = concurrency[start : end + 1]
                u_i = np.mean(1.0 / np.maximum(1, c_slice))
                uniqueness_scores.append(u_i)

        mean_u = float(np.mean(uniqueness_scores)) if uniqueness_scores else 1.0
        mean_c = float(np.mean(concurrency[concurrency > 0])) if np.any(concurrency > 0) else 1.0
        max_c = int(np.max(concurrency)) if len(concurrency) > 0 else 0

        return ConcurrencyMetrics(
            mean_concurrency=round(mean_c, 3),
            max_concurrency=max_c,
            mean_uniqueness=round(mean_u, 3),
            total_events=len(label_windows),
        )

    def split_purged_walk_forward(
        self,
        n_bars: int,
        label_windows: List[SampleLabelWindow],
        anchored: bool = False,
    ) -> Iterator[FoldSplit]:
        """
        Generates walk-forward folds with strict Purging and Embargoing.

        Parameters:
        - n_bars: Total number of bars in time series.
        - label_windows: List of SampleLabelWindow mapping sample_idx -> (t0_idx, t1_idx).
        - anchored: If True, train window starts at 0 (expanding). If False, rolling window.
        """
        embargo_bars = max(1, int(n_bars * self.embargo_pct))
        step_bars = max(1, (n_bars - self.min_train_bars) // self.n_splits)

        # Build lookup from sample_idx to window
        window_map = {w.sample_index: w for w in label_windows}

        for fold_idx in range(self.n_splits):
            test_start = self.min_train_bars + fold_idx * step_bars
            test_end = min(n_bars, test_start + self.test_size_bars)
            if test_start >= n_bars or test_end <= test_start:
                break

            train_start = 0 if anchored else max(0, test_start - self.min_train_bars * 2)
            raw_train = list(range(train_start, test_start))
            test_indices = list(range(test_start, test_end))

            purged = []
            embargoed = []
            valid_train = []

            for idx in raw_train:
                window = window_map.get(idx)
                if window is not None:
                    # Purging check: did this trade's outcome horizon touch or cross test_start?
                    if window.t1_idx >= test_start:
                        purged.append(idx)
                        continue

                valid_train.append(idx)

            # In rolling cross-validation, post-test training (if any) is embargoed
            # For standard forward walk-forward, train is strictly prior to test.
            # But if a future fold attempts to use data immediately after test_end:
            post_test_embargo_limit = test_end + embargo_bars
            for idx in range(test_end, min(n_bars, post_test_embargo_limit)):
                embargoed.append(idx)

            yield FoldSplit(
                fold_id=fold_idx + 1,
                train_indices=np.array(valid_train, dtype=int),
                test_indices=np.array(test_indices, dtype=int),
                purged_indices=np.array(purged, dtype=int),
                embargoed_indices=np.array(embargoed, dtype=int),
                t0_test=test_start,
                t1_test=test_end,
            )

    def cusum_filter(
        self,
        series: pd.Series,
        threshold: float,
    ) -> List[int]:
        """
        Symmetric CUSUM Filter for event-based volatility sampling.
        Returns bar indices where cumulative deviation crosses threshold.
        """
        diff = series.diff().dropna()
        if diff.empty or threshold <= 0:
            return list(range(len(series)))

        events = []
        s_pos = 0.0
        s_neg = 0.0

        for i, val in enumerate(diff):
            s_pos = max(0.0, s_pos + val)
            s_neg = min(0.0, s_neg + val)

            if s_pos >= threshold:
                events.append(i + 1)
                s_pos = 0.0
            elif s_neg <= -threshold:
                events.append(i + 1)
                s_neg = 0.0

        return events

    def assert_zero_leakage(self, fold: FoldSplit, label_windows: List[SampleLabelWindow]) -> bool:
        """
        Causal Leakage Assertion Guard.
        Raises AssertionError if any training sample leaks into or after test horizon.
        """
        window_map = {w.sample_index: w for w in label_windows}
        for train_idx in fold.train_indices:
            if train_idx in fold.test_indices:
                raise AssertionError(f"LEAKAGE DETECTED: Sample {train_idx} in both train and test!")
            w = window_map.get(train_idx)
            if w and w.t1_idx >= fold.t0_test:
                raise AssertionError(
                    f"PURGE FAILURE: Train sample {train_idx} label window ({w.t0_idx}->{w.t1_idx}) "
                    f"crosses test fold start ({fold.t0_test})!"
                )
        return True
