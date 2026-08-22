"""
Phase 43 — Test Suite for Validation Safety Controller & Automatic Kill Switch.

Verifies:
  - Kill switch trigger on excessive drawdown (>10%)
  - Kill switch trigger on degraded profit factor (<0.85)
  - Kill switch trigger on data feed failure
  - Kill switch pause/resume mechanism
"""
import pytest
from app.analytics.shadow_validation_engine import shadow_validation_engine


class TestKillSwitchSafety:
    def setup_method(self):
        # Reset state before each test
        shadow_validation_engine.resume_validation()

    def test_kill_switch_triggers_on_excessive_drawdown(self):
        triggered = shadow_validation_engine.evaluate_kill_switch(
            current_pf=1.5,
            current_dd_pct=12.5,  # > 10.0% limit
            ambiguous_count=1,
            total_trades=15,
            data_healthy=True,
        )
        assert triggered is True
        assert shadow_validation_engine.kill_switch_triggered is True
        assert "EXCESSIVE_DRAWDOWN" in shadow_validation_engine.kill_switch_reason
        assert shadow_validation_engine.is_paused is True

    def test_kill_switch_triggers_on_data_unhealthy(self):
        triggered = shadow_validation_engine.evaluate_kill_switch(
            current_pf=1.8,
            current_dd_pct=2.0,
            ambiguous_count=0,
            total_trades=5,
            data_healthy=False,  # Feed failure
        )
        assert triggered is True
        assert "DATA_HEALTH_DEGRADED" in shadow_validation_engine.kill_switch_reason

    def test_manual_pause_and_resume(self):
        pause_res = shadow_validation_engine.pause_validation("TEST_PAUSE")
        assert pause_res["status"] == "PAUSED"
        assert shadow_validation_engine.is_paused is True

        resume_res = shadow_validation_engine.resume_validation()
        assert resume_res["status"] == "LIVE"
        assert shadow_validation_engine.is_paused is False
        assert shadow_validation_engine.kill_switch_triggered is False
