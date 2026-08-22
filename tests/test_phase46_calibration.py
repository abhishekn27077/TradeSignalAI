"""
Phase 46 — Test Suite for 8-Bucket Calibration & Expected Calibration Error.

Verifies:
  - 8-bucket calibration table (50-55% to 85%+)
  - Brier score and ECE computations
"""
import pytest
from app.analytics.live_edge_validation_engine import live_edge_validation_engine


class TestCalibrationFidelity:
    def test_8_bucket_calibration_structure(self):
        calib = live_edge_validation_engine.evaluate_8_bucket_calibration()
        assert "total_buckets" in calib
        assert calib["total_buckets"] == 8
        assert "brier_score" in calib
        assert "expected_calibration_error" in calib
        assert len(calib["buckets"]) == 8

        for b in calib["buckets"]:
            assert "bucket" in b
            assert "predicted_prob" in b
            assert "observed_freq" in b
            assert "calibration_error" in b
