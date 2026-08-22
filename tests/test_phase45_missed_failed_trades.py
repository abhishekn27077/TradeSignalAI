"""
Phase 45 — Test Suite for Missed Trades, Failed Trades, and Model Scorecards.

Verifies:
  - Missed-trade MFE/MAE excursion analysis
  - Failed-trade root cause classifications
  - Model Scorecards accuracy, Brier scores, and alpha contributions
"""
import pytest
from app.analytics.daily_signal_journal import daily_signal_journal


class TestMissedFailedTradesAndModels:
    def test_missed_trade_mfe_mae_structure(self):
        missed = daily_signal_journal.get_missed_trades()
        assert "total_missed_audited" in missed
        assert "missed_trades" in missed
        assert len(missed["missed_trades"]) > 0

        for m in missed["missed_trades"]:
            assert "asset" in m
            assert "forecast_direction" in m
            assert "decision" in m
            assert m["decision"] == "NO_TRADE"
            assert "rejection_reason" in m
            assert "subsequent_move_pct" in m
            assert "mfe_pct" in m
            assert "mae_pct" in m
            assert "gate_impact" in m

    def test_failed_trade_root_cause_diagnostics(self):
        failed = daily_signal_journal.get_failed_trades()
        assert "total_failed_analyzed" in failed
        assert "failed_trades" in failed
        assert len(failed["failed_trades"]) > 0

        for f in failed["failed_trades"]:
            assert "asset" in f
            assert "outcome" in f
            assert f["outcome"] == "SL_HIT"
            assert "root_cause_category" in f
            assert "diagnosis" in f
            assert "affected_models" in f
            assert isinstance(f["affected_models"], list)

    def test_model_scorecard_and_ablation_matrix(self):
        models = daily_signal_journal.get_model_scorecard()
        assert "scorecards" in models
        assert "ablation_comparison" in models
        assert len(models["scorecards"]) >= 8

        for sc in models["scorecards"]:
            assert "model_name" in sc
            assert "direction_accuracy" in sc
            assert "brier_score" in sc
            assert "avg_confidence" in sc
            assert "contribution_pct" in sc
