import pytest
from datetime import datetime, timezone, timedelta
from app.analytics.calibration_engine import ConfidenceCalibrationEngine
from app.analytics.overtrading_engine import OvertradingDetector


def test_confidence_calibration_engine():
    engine = ConfidenceCalibrationEngine(num_bins=4, ece_threshold=0.15)

    # 100 well-calibrated synthetic predictions
    preds = [0.80]*50 + [0.60]*50
    targets = [1]*40 + [0]*10 + [1]*30 + [0]*20  # 80% and 60% win rates matching confidence!

    report = engine.evaluate_calibration(preds, targets)
    assert report.total_samples == 100
    assert report.brier_score <= 0.25
    assert report.expected_calibration_error_ece <= 0.05
    assert report.is_well_calibrated is True


def test_overtrading_detector():
    detector = OvertradingDetector(max_signals_per_session=3, max_signals_per_day=6)
    now = datetime.now(timezone.utc)

    # 4 signals generated in the last 2 hours (exceeds session limit of 3!)
    signals = [
        {"timestamp_utc": now - timedelta(minutes=100)},
        {"timestamp_utc": now - timedelta(minutes=60)},
        {"timestamp_utc": now - timedelta(minutes=30)},
        {"timestamp_utc": now - timedelta(minutes=5)},
    ]

    report = detector.evaluate_overtrading(signals, asset="EURUSD", current_time_utc=now)
    assert report.is_overtrading_detected is True
    assert report.clustering_risk_level == "HIGH"
    assert report.recommended_cooldown_minutes == 60
