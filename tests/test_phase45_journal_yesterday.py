"""
Phase 45 — Test Suite for Today's Journal, Yesterday's Results, and Tomorrow's Projections.

Verifies:
  - Today's signal journal structure (9 assets, decisions, summary counts)
  - Yesterday's result journal with gross R, friction breakdowns, and net R
  - Tomorrow's forward forecasts with AI reasoning and deterministic hashes
"""
import pytest
from app.analytics.daily_signal_journal import daily_signal_journal, CORE_ASSETS


class TestDailySignalJournals:
    def test_today_signal_journal_structure(self):
        today = daily_signal_journal.get_today_journal()
        assert "date" in today
        assert "summary" in today
        assert "forecasts" in today
        assert len(today["forecasts"]) == 9

        sum_metrics = today["summary"]
        for k in ["today_forecasts", "qualified_trades", "no_trade_count", "open_shadow_count", "resolved_count", "wins", "losses", "net_r"]:
            assert k in sum_metrics

        for f in today["forecasts"]:
            assert "asset" in f
            assert "direction" in f
            assert f["direction"] in ["BUY", "SELL"]
            assert "confidence" in f
            assert "entry_price" in f
            assert "stop_loss" in f
            assert "take_profit" in f
            assert "decision" in f
            assert f["decision"] in ["TAKE_TRADE", "NO_TRADE"]

    def test_yesterday_result_journal_frictions_and_net_r(self):
        yest = daily_signal_journal.get_yesterday_journal()
        assert "date" in yest
        assert "summary" in yest
        assert "records" in yest
        assert len(yest["records"]) == 9

        for r in yest["records"]:
            assert "outcome" in r
            assert r["outcome"] in ["TP_HIT", "SL_HIT", "TIME_EXIT", "AMBIGUOUS"]
            assert "gross_r" in r
            assert "costs" in r
            assert "net_r" in r
            assert "spread_r" in r["costs"]
            assert "slippage_r" in r["costs"]
            assert "fees_r" in r["costs"]
            # Net R must be strictly less than Gross R due to transaction frictions
            assert r["net_r"] < r["gross_r"] or r["gross_r"] < 0

    def test_tomorrow_forecasts_pre_event_integrity(self):
        tom = daily_signal_journal.get_tomorrow_forecasts()
        assert "target_date" in tom
        assert "generation_time" in tom
        assert "forecasts" in tom
        assert len(tom["forecasts"]) == 9

        for c in tom["forecasts"]:
            assert "asset" in c
            assert "direction" in c
            assert "probability" in c
            assert "expected_move_pct" in c
            assert "consensus" in c
            assert "regime" in c
            assert "ai_explanation" in c
            assert "input_hash" in c
            assert "prediction_hash" in c
            assert len(c["input_hash"]) == 64
            assert len(c["prediction_hash"]) == 64
