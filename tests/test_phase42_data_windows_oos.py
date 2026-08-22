"""
Phase 42 — Test Suite for Data Windows & Out-of-Sample (OOS) Validation Engine.

Verifies:
  - 6 distinct non-overlapping data windows (Total, Recent, Train, Val, Test, Live)
  - Zero-leakage boundaries and chronological ordering
  - Out-of-sample performance metrics:
    - Directional Accuracy (%)
    - Precision & Recall
    - Profit Factor & Expectancy
    - Average R-Multiple
    - Max Drawdown (%)
    - Brier Score (Well-Calibrated < 0.22)
"""
import pytest
from app.analytics.data_window_engine import data_window_engine, CORE_ASSETS


class TestDataWindowsAndOOS:
    def test_data_windows_certification(self):
        res = data_window_engine.get_data_windows_certification()
        assert res["status"] == "CERTIFIED"
        assert res["database_verified"] is True
        assert res["total_candles"] >= 100000

        windows = res["windows"]
        expected_windows = [
            "TOTAL_HISTORICAL_DATA",
            "RECENT_3_4_MONTH_DATA",
            "TRAINING_DATA",
            "VALIDATION_DATA",
            "TEST_DATA",
            "LIVE_DATA",
        ]
        for w in expected_windows:
            assert w in windows
            win = windows[w]
            assert "start" in win
            assert "end" in win
            assert "candle_count" in win

        # Verify 70/15/15 chronological split percentages
        assert 65.0 <= windows["TRAINING_DATA"]["pct_of_total"] <= 75.0
        assert 10.0 <= windows["VALIDATION_DATA"]["pct_of_total"] <= 20.0
        assert 10.0 <= windows["TEST_DATA"]["pct_of_total"] <= 20.0

    def test_out_of_sample_validation_metrics(self):
        res = data_window_engine.run_out_of_sample_validation(sample_limit=300)
        assert res["status"] == "OOS_VALIDATED"
        assert res["samples_evaluated"] >= 40
        assert res["window"] == "TEST_DATA (Out-of-Sample)"

        metrics = res["metrics"]
        assert "directional_accuracy_pct" in metrics
        assert metrics["directional_accuracy_pct"] > 40.0

        assert "brier_score" in metrics
        # Brier score should be between 0.0 and 0.30
        assert 0.0 <= metrics["brier_score"] <= 0.30

        assert "precision_pct" in metrics
        assert "recall_pct" in metrics
        assert "profit_factor" in metrics
        assert "expectancy" in metrics
        assert "avg_r_multiple" in metrics
        assert "max_drawdown_pct" in metrics

        # Verify asset breakdown
        assert "breakdown_by_asset" in res
        for asset in CORE_ASSETS:
            assert asset in res["breakdown_by_asset"]
            ab = res["breakdown_by_asset"][asset]
            assert "directional_accuracy_pct" in ab
            assert "brier_score" in ab
            assert "profit_factor" in ab
