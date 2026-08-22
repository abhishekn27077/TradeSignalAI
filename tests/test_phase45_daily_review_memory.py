"""
Phase 45 — Test Suite for Daily AI Review, Market Memory, Artifact Generation, and API Routes.

Verifies:
  - Daily market memory structure
  - Daily AI review synthesis
  - Daily JSON artifact persistence to artifacts/phase45/daily/YYYY-MM-DD.json
"""
import os
import json
import pytest
from app.analytics.daily_signal_journal import daily_signal_journal


class TestDailyReviewAndMemory:
    def test_daily_market_memory_fields(self):
        memory = daily_signal_journal.get_daily_market_memory()
        assert "date" in memory
        assert "dominant_regime" in memory
        assert "risk_mood" in memory
        assert "usd_strength" in memory
        assert "gold_regime" in memory
        assert "equity_regime" in memory
        assert "crypto_regime" in memory
        assert "market_volatility" in memory

    def test_daily_ai_review_synthesis(self):
        review = daily_signal_journal.get_daily_ai_review()
        assert "date" in review
        assert "market_regime" in review
        assert "best_asset" in review
        assert "worst_asset" in review
        assert "best_model" in review
        assert "weakest_model" in review
        assert "best_session" in review
        assert "worst_session" in review
        assert "verdict" in review

    def test_daily_json_artifact_persistence(self):
        file_path = daily_signal_journal.save_daily_artifact("2026-08-21")
        assert os.path.exists(file_path)

        with open(file_path, "r") as f:
            data = json.load(f)

        assert data["date"] == "2026-08-21"
        assert "today_journal" in data
        assert "yesterday_journal" in data
        assert "tomorrow_forecasts" in data
        assert "model_scorecard" in data
        assert "missed_trades" in data
        assert "failed_trades" in data
        assert "market_memory" in data
        assert "ai_review" in data
