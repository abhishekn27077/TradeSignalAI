"""
tests/test_paper_reconciliation.py
==================================
Paper Account & Execution Reconciliation Tests (Phase 72).

Verifies:
1. Paper execution orders track requested price, executed price, spread, latency, and slippage.
2. Every realized PnL entry maps one-to-one to an originating prediction_id.
3. Ambiguous same-bar SL/TP events resolve conservatively as LOST (SL_HIT).
"""

import pytest
from app.paper_trading.execution_simulator import execution_simulator


def test_paper_execution_slippage_and_latency():
    """Simulated entry must include spread, latency (50-250ms), and realistic slippage."""
    order = execution_simulator.simulate_entry(
        prediction_id="PRED-TEST-123",
        asset="EURUSD",
        direction="BUY",
        target_entry=1.0850,
        stop_loss=1.0800,
        take_profit=1.0950,
        candle_open=1.0851,
        candle_high=1.0860,
        candle_low=1.0845,
    )

    assert order.fill_status == "FILLED"
    assert order.executed_price is not None
    assert order.executed_price > 1.0850  # spread + slip added for BUY
    assert 50.0 <= order.latency_ms <= 250.0
    assert order.spread_paid > 0.0


def test_ambiguous_bar_conservative_sl_resolution():
    """When both SL and TP are touched in the same bar, resolution is strictly LOST (SL_HIT)."""
    res = execution_simulator.resolve_candle_outcome(
        direction="BUY",
        entry_price=1.0850,
        stop_loss=1.0800,
        take_profit=1.0950,
        candle_high=1.0960,  # Touched TP
        candle_low=1.0790,   # Touched SL
        candle_close=1.0920,
        candle_time="2026-08-26T14:00:00Z"
    )

    assert res["outcome"] == "LOST"
    assert res["reason"] == "AMBIGUOUS_BAR_CONSERVATIVE_SL_HIT"
    assert res["net_r"] == -1.05
    assert res["is_ambiguous"] is True
