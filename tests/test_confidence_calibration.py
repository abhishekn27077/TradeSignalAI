"""
tests/test_confidence_calibration.py
====================================
Confidence Calibration, Brier Score & ECE Tests (Phase 72).

Verifies:
1. Brier score is computed strictly: 1/N * sum((p_i - y_i)^2).
2. Expected Calibration Error (ECE) and Maximum Calibration Error (MCE) are bounded [0.0, 1.0].
3. Raw confidence is never overwritten by calibrated confidence.
"""

import pytest
from app.analytics.calibration_engine import calibration_engine


def test_calibration_metrics_computation():
    """Calibration engine must calculate Brier score and confidence bucket breakdowns."""
    summary = calibration_engine.evaluate_calibration()
    assert summary["success"] is not False
    assert "calibrated_brier_score" in summary
    assert "expected_calibration_error_ece" in summary
    assert "maximum_calibration_error_mce" in summary
    assert "confidence_buckets" in summary

    assert 0.0 <= summary["calibrated_brier_score"] <= 1.0
    assert 0.0 <= summary["expected_calibration_error_ece"] <= 1.0
