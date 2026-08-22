"""
Phase 43 — Test Suite for Statistical Edge, Bootstrap CIs & Confidence Calibration.

Verifies:
  - 1,000-iteration bootstrap confidence intervals
  - 8-bucket confidence calibration calculation & Brier score
  - Multi-dimensional breakdown coverage (Regime, Session, Asset, Events, News, Models)
"""
import pytest
from app.analytics.shadow_statistics_engine import shadow_statistics_engine


class TestStatisticsAndCalibration:
    def test_bootstrap_significance_ci(self):
        stats = shadow_statistics_engine.compute_bootstrap_significance(n_iterations=1000)
        assert stats["iterations"] == 1000
        assert "expectancy_95_ci" in stats
        assert len(stats["expectancy_95_ci"]) == 2
        assert stats["expectancy_95_ci"][0] <= stats["expectancy_95_ci"][1]
        assert "classification" in stats
        assert stats["classification"] in ["INSUFFICIENT_EVIDENCE", "NEUTRAL", "PROMISING", "STATISTICALLY_SUPPORTED"]

    def test_8_bucket_calibration_structure(self):
        cal = shadow_statistics_engine.compute_confidence_calibration()
        assert "buckets" in cal
        assert len(cal["buckets"]) == 8
        expected_buckets = ["50-55%", "55-60%", "60-65%", "65-70%", "70-75%", "75-80%", "80-85%", "85%+"]
        for b, exp in zip(cal["buckets"], expected_buckets):
            assert b["bucket"] == exp
            assert "predicted_probability" in b
            assert "actual_accuracy" in b
            assert "brier_score" in b

    def test_multi_dimensional_breakdowns(self):
        # Assets
        as_data = shadow_statistics_engine.get_asset_breakdown()
        assert "best_current_edge" in as_data
        assert len(as_data["assets"]) == 9

        # Regimes
        rg_data = shadow_statistics_engine.get_regime_breakdown()
        assert len(rg_data["regimes"]) == 5

        # Sessions
        se_data = shadow_statistics_engine.get_session_breakdown()
        assert len(se_data["sessions"]) == 4

        # Events
        ev_data = shadow_statistics_engine.get_economic_events_breakdown()
        assert ev_data["total_events_tracked"] == 29

        # News
        nw_data = shadow_statistics_engine.get_news_impact_breakdown()
        assert "by_market_mood" in nw_data
        assert "by_sentiment" in nw_data

        # Forward Models
        mo_data = shadow_statistics_engine.get_forward_model_contribution()
        assert len(mo_data["models"]) == 5
