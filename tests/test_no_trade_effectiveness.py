"""
tests/test_no_trade_effectiveness.py
====================================
NO_TRADE Quality & Counterfactual Evaluation Tests (Phase 72).

Verifies:
1. NO_TRADE is evaluated as an active capital protection decision.
2. Counterfactual analysis quantifies losses avoided vs potential wins missed.
"""

import pytest
from app.analytics.no_trade_engine import no_trade_engine


def test_no_trade_effectiveness_computation():
    """NoTradeEngine must report total NO_TRADE decisions and net capital preserved."""
    summary = no_trade_engine.evaluate_no_trade_effectiveness()
    assert summary["success"] is True
    assert summary["total_no_trade_decisions"] > 0
    assert "counterfactual_losses_avoided" in summary
    assert "estimated_capital_saved_r" in summary
    assert summary["avoided_loss_rate_pct"] > 50.0
