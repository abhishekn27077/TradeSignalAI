import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class CalibrationBucket:
    bin_lower: float
    bin_upper: float
    predicted_confidence_mean: float
    actual_win_rate: float
    sample_count: int
    brier_score_contribution: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bin_range": f"{int(self.bin_lower*100)}-{int(self.bin_upper*100)}%",
            "predicted_confidence_mean": round(float(self.predicted_confidence_mean), 3),
            "actual_win_rate": round(float(self.actual_win_rate), 3),
            "sample_count": self.sample_count,
            "brier_contribution": round(float(self.brier_score_contribution), 4)
        }


@dataclass
class CalibrationReport:
    total_samples: int
    brier_score: float  # Mean Squared Error between confidence and outcome
    expected_calibration_error_ece: float
    is_well_calibrated: bool
    buckets: List[CalibrationBucket] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_samples": self.total_samples,
            "brier_score": round(float(self.brier_score), 4),
            "expected_calibration_error_ece": round(float(self.expected_calibration_error_ece), 4),
            "is_well_calibrated": self.is_well_calibrated,
            "buckets": [b.to_dict() for b in self.buckets],
            "details": self.details
        }


class ConfidenceCalibrationEngine:
    """
    Confidence Score Reliability & Probability Calibration Engine.
    Computes Brier Scores, Reliability Bins, and Expected Calibration Error (ECE).
    """

    def __init__(self, num_bins: int = 5, ece_threshold: float = 0.15):
        self.num_bins = num_bins
        self.ece_threshold = ece_threshold

    def evaluate_calibration(
        self,
        predicted_confidences: List[float],
        actual_outcomes: List[int]  # 1 for win, 0 for loss
    ) -> CalibrationReport:
        if not predicted_confidences or len(predicted_confidences) != len(actual_outcomes):
            return CalibrationReport(0, 0.0, 0.0, False, [])

        preds = np.array(predicted_confidences)
        targets = np.array(actual_outcomes)
        n = len(preds)

        # 1. Brier Score = (1/N) * sum((p - y)^2)
        brier = float(np.mean((preds - targets) ** 2))

        # 2. Reliability Bins
        bins = np.linspace(0.5, 1.0, self.num_bins + 1)
        buckets = []
        total_ece = 0.0

        for i in range(len(bins) - 1):
            low, high = bins[i], bins[i + 1]
            mask = (preds >= low) & (preds <= high if i == len(bins) - 2 else preds < high)
            count = int(mask.sum())

            if count > 0:
                bin_preds = preds[mask]
                bin_targets = targets[mask]
                mean_p = float(bin_preds.mean())
                mean_y = float(bin_targets.mean())
                ece_bin = abs(mean_p - mean_y) * (count / n)
                total_ece += ece_bin

                brier_contrib = float(np.mean((bin_preds - bin_targets) ** 2)) * (count / n)

                buckets.append(CalibrationBucket(
                    bin_lower=low,
                    bin_upper=high,
                    predicted_confidence_mean=mean_p,
                    actual_win_rate=mean_y,
                    sample_count=count,
                    brier_score_contribution=brier_contrib
                ))

        is_calibrated = (total_ece <= self.ece_threshold) and (brier <= 0.25)

        return CalibrationReport(
            total_samples=n,
            brier_score=brier,
            expected_calibration_error_ece=total_ece,
            is_well_calibrated=is_calibrated,
            buckets=buckets,
            details={"bins_evaluated": len(buckets)}
        )
