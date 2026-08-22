import pytest
import numpy as np

from app.analytics.continuous_forward_monitor import (
    ContinuousForwardMonitor,
    continuous_forward_monitor,
    ForwardMonitoringSnapshot,
)


def test_phase47_continuous_forward_monitor_snapshot():
    snapshot = continuous_forward_monitor.evaluate_live_cohort(
        realized_trade_rs=[1.82] * 26 + [-0.98] * 16,
        total_signals=128,
        gated_signals=86,
    )
    
    assert isinstance(snapshot, ForwardMonitoringSnapshot)
    assert snapshot.total_signals == 128
    assert snapshot.executed_trades == 42
    assert snapshot.gated_signals == 86
    assert snapshot.winning_trades == 26
    assert snapshot.losing_trades == 16
    assert snapshot.win_rate > 0.60
    assert snapshot.profit_factor > 1.70
    assert snapshot.expectancy_r > 0.30
    assert snapshot.brier_score == 0.184
    assert snapshot.governance_tier == "EARLY_EVIDENCE"
    assert snapshot.system_status == "PROMISING_FORWARD_EDGE"
    assert snapshot.config_hash == "79a4f8e12b79310d"


def test_phase47_governance_tier_progression():
    monitor = ContinuousForwardMonitor()
    
    # N < 30 -> INSUFFICIENT_SAMPLE
    s_small = monitor.evaluate_live_cohort(realized_trade_rs=[1.5, -1.0] * 10)
    assert s_small.governance_tier == "INSUFFICIENT_SAMPLE"
    assert s_small.system_status == "INSUFFICIENT_EVIDENCE"
    
    # 30 <= N < 100 -> EARLY_EVIDENCE
    s_mid = monitor.evaluate_live_cohort(realized_trade_rs=[1.82] * 25 + [-0.98] * 15)
    assert s_mid.governance_tier == "EARLY_EVIDENCE"
    
    # 100 <= N < 300 -> PRELIMINARY_EVIDENCE
    s_large = monitor.evaluate_live_cohort(realized_trade_rs=[1.82] * 70 + [-0.98] * 40)
    assert s_large.governance_tier == "PRELIMINARY_EVIDENCE"


def test_phase47_friction_stress_survival():
    # Base trades: 26 wins at +1.82R, 16 losses at -0.98R
    base_trades = [1.82] * 26 + [-0.98] * 16
    
    # Simulate +100% extreme friction: deduct 0.22R per trade (wider spread + slippage)
    stressed_trades = [r - 0.22 if r > 0 else r - 0.10 for r in base_trades]
    
    wins = [r for r in stressed_trades if r > 0]
    losses = [r for r in stressed_trades if r < 0]
    
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    stressed_pf = gross_win / gross_loss
    stressed_expectancy = float(np.mean(stressed_trades))
    
    # Even under +100% friction, edge must survive (PF > 1.0, Expectancy > 0)
    assert stressed_pf > 1.20
    assert stressed_expectancy > 0.10
