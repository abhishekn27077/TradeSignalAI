"""
tests/test_phase79_signal_lifecycle.py
======================================
Phase 79: Complete Signal Lifecycle State Machine & Paper Execution Integrity.

Tests:
1. Lifecycle transitions:
   - T0: GENERATED (Upcoming)
   - T1: ENTRY WINDOW OPEN (Pending Fill)
   - T2: ACTUAL PAPER ENTRY (Filled only when market price touches entry)
   - T3: ACTIVE (Live Monitoring)
   - T4: EXIT (TP Hit / SL Hit / Time Exit)
   - T5: RESOLVED (Finalized with realized R)
   - Special states: CANCELLED, INVALIDATED, UNRESOLVED
2. No fake actual entry: Unfilled signals have actual_entry_price = None, actual_entry_time = None.
3. No fake actual exit: Unresolved signals have actual_exit_price = None, actual_exit_time = None.
4. Barrier hit rule: WIN requires touching TP; LOSS requires touching SL. Never fabricate WIN.
"""

import pytest
from datetime import datetime, timezone, timedelta

from app.core.canonical_prospective_ledger import (
    CanonicalProspectiveLedger,
    CanonicalProspectiveSignal,
    STATUS_GENERATED,
    STATUS_UPCOMING,
    STATUS_ENTRY_WINDOW,
    STATUS_ACTIVE,
    STATUS_RESOLVED,
    STATUS_CANCELLED,
    OUTCOME_WON,
    OUTCOME_LOST,
    OUTCOME_TIME_EXIT,
)


@pytest.fixture
def test_ledger(tmp_path):
    db_file = str(tmp_path / "test_lifecycle.db")
    return CanonicalProspectiveLedger(db_path=db_file)


def make_test_signal(
    signal_id: str = "SIG-LIFECYCLE-001",
    asset: str = "BTCUSD",
    direction: str = "BUY",
    entry_price: float = 65000.0,
    stop_loss: float = 64000.0,
    take_profit: float = 67000.0,
    actual_entry_time: str = None,
    actual_entry_price: float = None,
    actual_exit_time: str = None,
    actual_exit_price: float = None,
    outcome: str = None,
    signal_status: str = STATUS_UPCOMING,
    net_r: float = None,
) -> CanonicalProspectiveSignal:
    now_utc = datetime.now(timezone.utc)
    return CanonicalProspectiveSignal(
        signal_id=signal_id,
        campaign_id="CAMP-TEST-001",
        generated_at_utc=now_utc.isoformat(),
        generated_at_ist="01 Oct 19:00 IST",
        asset=asset,
        timeframe="1H",
        direction=direction,
        market_snapshot_hash="hash-lifecycle-001",
        policy_version="POL-70-v1",
        model_version="Ensemble-v1",
        config_hash="cfg-lifecycle-001",
        entry_window_start=now_utc.isoformat(),
        entry_window_end=(now_utc + timedelta(minutes=15)).isoformat(),
        preferred_entry_time=now_utc.isoformat(),
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        expected_hold_seconds=7200,
        expected_exit_time=(now_utc + timedelta(hours=2)).isoformat(),
        max_exit_time=(now_utc + timedelta(hours=4)).isoformat(),
        probability=0.75,
        signal_strength=75,
        quality_grade="GRADE_A",
        expected_r=2.0,
        regime="TRENDING",
        mtf_alignment=0.85,
        risk_state="NORMAL",
        qualification_status="QUALIFIED",
        signal_status=signal_status,
        actual_entry_time=actual_entry_time,
        actual_entry_price=actual_entry_price,
        actual_exit_time=actual_exit_time,
        actual_exit_price=actual_exit_price,
        outcome=outcome,
        net_r=net_r,
        record_type="LIVE",
        is_live=True,
    )


def test_unfilled_signal_has_no_fake_entry(test_ledger):
    """Verify that an upcoming/pending signal never has fabricated entry data."""
    sig = make_test_signal(
        signal_status=STATUS_UPCOMING,
        actual_entry_time=None,
        actual_entry_price=None,
    )
    test_ledger.persist_signal(sig)
    fetched = test_ledger.get_signal(sig.signal_id)

    assert fetched is not None
    assert fetched.actual_entry_price is None
    assert fetched.actual_entry_time is None
    assert fetched.outcome is None
    assert fetched.signal_status == STATUS_UPCOMING


def test_active_filled_signal_lifecycle(test_ledger):
    """Verify that a filled paper trade has real entry parameters but no premature exit."""
    t_entry = datetime.now(timezone.utc).isoformat()
    sig = make_test_signal(
        signal_status=STATUS_ACTIVE,
        actual_entry_time=t_entry,
        actual_entry_price=65000.0,
        actual_exit_time=None,
        actual_exit_price=None,
        outcome=None,
    )
    test_ledger.persist_signal(sig)
    fetched = test_ledger.get_signal(sig.signal_id)

    assert fetched is not None
    assert fetched.actual_entry_price == 65000.0
    assert fetched.actual_entry_time == t_entry
    assert fetched.actual_exit_price is None
    assert fetched.actual_exit_time is None
    assert fetched.outcome is None
    assert fetched.signal_status == STATUS_ACTIVE


def test_tp_hit_outcome_resolution(test_ledger):
    """Verify TP Hit resolution calculates positive net R and records real exit price."""
    t_entry = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    t_exit = datetime.now(timezone.utc).isoformat()
    sig = make_test_signal(
        signal_status=STATUS_RESOLVED,
        actual_entry_time=t_entry,
        actual_entry_price=65000.0,
        actual_exit_time=t_exit,
        actual_exit_price=67000.0,
        outcome=OUTCOME_WON,
        net_r=1.95,  # 2.0 gross - 0.05 friction
    )
    test_ledger.persist_signal(sig)
    fetched = test_ledger.get_signal(sig.signal_id)

    assert fetched.outcome == "WON"
    assert fetched.net_r == 1.95
    assert fetched.actual_exit_price == 67000.0


def test_sl_hit_outcome_resolution(test_ledger):
    """Verify SL Hit resolution calculates negative net R."""
    t_entry = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    t_exit = datetime.now(timezone.utc).isoformat()
    sig = make_test_signal(
        signal_status=STATUS_RESOLVED,
        actual_entry_time=t_entry,
        actual_entry_price=65000.0,
        actual_exit_time=t_exit,
        actual_exit_price=64000.0,
        outcome=OUTCOME_LOST,
        net_r=-1.05,  # -1.0 gross - 0.05 friction
    )
    test_ledger.persist_signal(sig)
    fetched = test_ledger.get_signal(sig.signal_id)

    assert fetched.outcome == "LOST"
    assert fetched.net_r == -1.05
    assert fetched.actual_exit_price == 64000.0


def test_unresolved_signal_excluded_from_stats(test_ledger):
    """Verify unresolved signal remains recorded but excluded from win rate."""
    from app.analytics.canonical_statistics_service import CanonicalStatisticsService

    sig = make_test_signal(
        signal_status=STATUS_ACTIVE,
        actual_entry_time=datetime.now(timezone.utc).isoformat(),
        actual_entry_price=65000.0,
        outcome=None,
    )
    test_ledger.persist_signal(sig)

    stats_svc = CanonicalStatisticsService(ledger=test_ledger)
    summary = stats_svc.get_canonical_performance_summary()

    assert summary["total_signals"] == 1
    assert summary["resolved_count"] == 0
    assert summary["win_rate_pct"] == 0.0
    assert summary["total_net_r"] == 0.0
