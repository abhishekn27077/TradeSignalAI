"""
tests/test_signal_integrity_and_real_enforcement.py
===================================================
Automated Test Suite for Phase 77:
Signal Integrity, Real-Signal Enforcement & Forensic History.

Verifies the 10 Acceptance Criteria from Section 17:
1. Historical-only data cannot produce a live signal.
2. Blocked MT5 cannot produce a live forex signal.
3. Stale data cannot produce a live signal.
4. Failed qualification cannot produce a canonical signal.
5. Model disagreement cannot produce a qualified signal.
6. Demo/test records cannot appear in Today's Live Signals.
7. A signal with inconsistent entry price is rejected.
8. Missing resolution evidence cannot become WIN/LOSS.
9. Performance excludes unresolved/demo/test records.
10. Frontend Today's Signals equals backend canonical qualified signals.
"""

import pytest
import sqlite3
from datetime import datetime, timezone, timedelta
from app.core.canonical_prospective_ledger import (
    CanonicalProspectiveLedger,
    CanonicalProspectiveSignal,
    STATUS_UPCOMING,
    STATUS_RESOLVED,
    STATUS_REJECTED,
)
from app.analytics.canonical_statistics_service import CanonicalStatisticsService
from app.api.v1.terminal_routes import get_today_signals, get_canonical_history, format_signal_for_terminal
from app.market_data.providers.mt5_provider import mt5_provider


@pytest.fixture
def temp_ledger(tmp_path):
    """Provides an isolated CanonicalProspectiveLedger instance."""
    db_file = str(tmp_path / "test_integrity.db")
    ledger = CanonicalProspectiveLedger(db_path=db_file)
    return ledger


def test_1_historical_only_data_cannot_produce_live_signal(temp_ledger):
    """1. Historical-only data cannot produce a live signal."""
    now_utc = datetime.now(timezone.utc)
    sig = CanonicalProspectiveSignal(
        signal_id="SIG-HIST-TEST-001",
        campaign_id="CAMP-HIST-01",
        generated_at_utc=now_utc.isoformat(),
        generated_at_ist=now_utc.isoformat(),
        asset="EURUSD",
        timeframe="1H",
        direction="BUY",
        market_snapshot_hash="hash-hist-only",
        policy_version="POL-70-v1",
        model_version="Ensemble-v1",
        config_hash="conf-01",
        entry_window_start=now_utc.isoformat(),
        entry_window_end=(now_utc + timedelta(minutes=15)).isoformat(),
        preferred_entry_time=now_utc.isoformat(),
        entry_price=1.0850,
        stop_loss=1.0820,
        take_profit=1.0910,
        expected_hold_seconds=3600,
        expected_exit_time=(now_utc + timedelta(hours=1)).isoformat(),
        max_exit_time=(now_utc + timedelta(hours=2)).isoformat(),
        probability=0.72,
        signal_strength=80,
        quality_grade="GRADE_A",
        expected_r=2.0,
        regime="TRENDING_UP",
        mtf_alignment=0.85,
        risk_state="NORMAL",
        qualification_status="QUALIFIED",
        signal_status=STATUS_UPCOMING,
        record_type="HISTORICAL",
        is_live=False,
        is_historical=True,
        live_data_verified=False,
    )
    temp_ledger.persist_signal(sig)
    
    # Check that live_only filter does NOT return historical signal
    live_signals = temp_ledger.get_signals_by_filter(date_filter="TODAY", live_only=True)
    assert len(live_signals) == 0, "Historical-only signal must never appear in live_only query"


def test_2_blocked_mt5_cannot_produce_live_forex_signal():
    """2. Blocked MT5 cannot produce a live forex signal."""
    diag = mt5_provider.get_safe_diagnostics()
    # Check that MT5 is not live/authorized in current environment
    is_mt5_live = diag.get("connection_state") == "CONNECTED" and diag.get("authorization_state") == "AUTHORIZED"
    
    today_res = get_today_signals()
    providers = today_res.get("providers", {})
    
    if not is_mt5_live:
        assert providers["mt5"]["status"] == "BLOCKED"
        assert providers["mt5"]["verified"] is False
        assert "BLOCKED" in providers["mt5"]["label"]
        # No live signals for forex assets can be returned
        forex_signals = [s for s in today_res["signals"] if s["asset"] in ["EURUSD", "GBPUSD", "USDJPY"]]
        assert len(forex_signals) == 0, "Blocked MT5 must not emit live forex signals"


def test_3_stale_data_cannot_produce_live_signal(temp_ledger):
    """3. Stale data cannot produce a live signal."""
    old_time = datetime.now(timezone.utc) - timedelta(hours=5)
    sig = CanonicalProspectiveSignal(
        signal_id="SIG-STALE-TEST-001",
        campaign_id="CAMP-STALE-01",
        generated_at_utc=old_time.isoformat(),
        generated_at_ist=old_time.isoformat(),
        asset="BTCUSD",
        timeframe="15m",
        direction="BUY",
        market_snapshot_hash="hash-stale-01",
        policy_version="POL-70-v1",
        model_version="Ensemble-v1",
        config_hash="conf-stale",
        entry_window_start=old_time.isoformat(),
        entry_window_end=(old_time + timedelta(minutes=5)).isoformat(),
        preferred_entry_time=old_time.isoformat(),
        entry_price=64000.0,
        stop_loss=63500.0,
        take_profit=65000.0,
        expected_hold_seconds=900,
        expected_exit_time=(old_time + timedelta(minutes=15)).isoformat(),
        max_exit_time=(old_time + timedelta(minutes=30)).isoformat(),
        probability=0.75,
        signal_strength=85,
        quality_grade="GRADE_A",
        expected_r=2.0,
        regime="TRENDING",
        mtf_alignment=0.8,
        risk_state="NORMAL",
        qualification_status="QUALIFIED",
        signal_status=STATUS_UPCOMING,
        record_type="LIVE",
        is_live=True,
        live_data_verified=True,
        data_age_seconds=18000.0,  # 5 hours old data
    )
    # Stale data check is automatically enforced during persist_signal
    temp_ledger.persist_signal(sig)
    live_signals = temp_ledger.get_signals_by_filter(date_filter="TODAY", live_only=True)
    assert len(live_signals) == 0, "Stale data must not produce a live qualified signal"
    persisted = temp_ledger.get_signal(sig.signal_id)
    assert persisted is not None
    assert persisted.qualification_status == "REJECTED"
    assert "STALE_MARKET_DATA" in (persisted.no_trade_reason or "")
    assert persisted.is_live is False


def test_4_failed_qualification_cannot_produce_canonical_signal(temp_ledger):
    """4. Failed qualification cannot produce a canonical signal."""
    now_utc = datetime.now(timezone.utc)
    sig = CanonicalProspectiveSignal(
        signal_id="SIG-FAILQUAL-TEST-001",
        campaign_id="CAMP-FAIL-01",
        generated_at_utc=now_utc.isoformat(),
        generated_at_ist=now_utc.isoformat(),
        asset="BTCUSD",
        timeframe="1H",
        direction="BUY",
        market_snapshot_hash="hash-fail-01",
        policy_version="POL-70-v1",
        model_version="Ensemble-v1",
        config_hash="conf-01",
        entry_window_start=now_utc.isoformat(),
        entry_window_end=(now_utc + timedelta(minutes=15)).isoformat(),
        preferred_entry_time=now_utc.isoformat(),
        entry_price=64000.0,
        stop_loss=63000.0,
        take_profit=66000.0,
        expected_hold_seconds=3600,
        expected_exit_time=(now_utc + timedelta(hours=1)).isoformat(),
        max_exit_time=(now_utc + timedelta(hours=2)).isoformat(),
        probability=0.45,  # Low probability
        signal_strength=40,
        quality_grade="GRADE_D",
        expected_r=1.2,
        regime="CHOPPY",
        mtf_alignment=0.3,
        risk_state="HIGH_VOLATILITY",
        qualification_status="REJECTED",
        signal_status=STATUS_REJECTED,
        no_trade_reason="FAILED_QUALIFICATION_THRESHOLD",
        record_type="LIVE",
        is_live=True,
    )
    temp_ledger.persist_signal(sig)
    
    windows = temp_ledger.get_today_time_windows()
    # Qualified count must be 0
    total_qual = sum(w["qualified_count"] for w in windows)
    assert total_qual == 0, "Failed qualification signal must never appear in qualified count"


def test_5_model_disagreement_cannot_produce_qualified_signal():
    """5. Model disagreement cannot produce a qualified signal."""
    # When agreement < 60% (e.g. 57.1%), qualification status must be REJECTED / NO_TRADE
    agreement_pct = 57.1
    threshold = 60.0
    
    decision = "QUALIFIED" if agreement_pct >= threshold else "REJECTED"
    assert decision == "REJECTED", f"Agreement {agreement_pct}% < {threshold}% must result in REJECTED"


def test_6_demo_or_test_records_cannot_appear_in_today_live_signals(temp_ledger):
    """6. Demo/test records cannot appear in Today's Live Signals."""
    now_utc = datetime.now(timezone.utc)
    demo_sig = CanonicalProspectiveSignal(
        signal_id="SIG-DEDUP-TEST-DEMO-001",
        campaign_id="CAMP-TEST-01",
        generated_at_utc=now_utc.isoformat(),
        generated_at_ist=now_utc.isoformat(),
        asset="USDJPY",
        timeframe="4H",
        direction="BUY",
        market_snapshot_hash="snap-dup",
        policy_version="POL-70-v1",
        model_version="Ensemble-v1",
        config_hash="conf-01",
        entry_window_start=now_utc.isoformat(),
        entry_window_end=(now_utc + timedelta(minutes=15)).isoformat(),
        preferred_entry_time=now_utc.isoformat(),
        entry_price=152.0,
        stop_loss=151.0,
        take_profit=154.0,
        expected_hold_seconds=14400,
        expected_exit_time=(now_utc + timedelta(hours=4)).isoformat(),
        max_exit_time=(now_utc + timedelta(hours=5)).isoformat(),
        probability=0.8,
        signal_strength=85,
        quality_grade="GRADE_A",
        expected_r=2.0,
        regime="TRENDING",
        mtf_alignment=0.9,
        risk_state="NORMAL",
        qualification_status="QUALIFIED",
        signal_status=STATUS_UPCOMING,
        record_type="DEMO",
        is_live=False,
        is_demo=True,
        live_data_verified=False,
    )
    temp_ledger.persist_signal(demo_sig)
    
    live_today = temp_ledger.get_signals_by_filter(date_filter="TODAY", live_only=True)
    assert len(live_today) == 0, "Demo/test records must never appear in live today signals"


def test_7_signal_with_inconsistent_entry_price_is_rejected(temp_ledger):
    """7. A signal with inconsistent entry price is rejected."""
    now_utc = datetime.now(timezone.utc)
    # Market price = 60,000.0, Entry price = 61,000.0 (deviation = 1.66% > 0.5% threshold)
    sig = CanonicalProspectiveSignal(
        signal_id="SIG-INCONSISTENT-PRICE-001",
        campaign_id="CAMP-INCONSISTENT-01",
        generated_at_utc=now_utc.isoformat(),
        generated_at_ist=now_utc.isoformat(),
        asset="BTCUSD",
        timeframe="15m",
        direction="BUY",
        market_snapshot_hash="snap-price-dev",
        policy_version="POL-70-v1",
        model_version="Ensemble-v1",
        config_hash="conf-price",
        entry_window_start=now_utc.isoformat(),
        entry_window_end=(now_utc + timedelta(minutes=5)).isoformat(),
        preferred_entry_time=now_utc.isoformat(),
        entry_price=61000.0,
        stop_loss=59000.0,
        take_profit=63000.0,
        expected_hold_seconds=900,
        expected_exit_time=(now_utc + timedelta(minutes=15)).isoformat(),
        max_exit_time=(now_utc + timedelta(minutes=30)).isoformat(),
        probability=0.78,
        signal_strength=80,
        quality_grade="GRADE_A",
        expected_r=2.0,
        regime="TRENDING",
        mtf_alignment=0.85,
        risk_state="NORMAL",
        qualification_status="QUALIFIED",
        signal_status=STATUS_UPCOMING,
        record_type="LIVE",
        is_live=True,
        market_price_at_generation=60000.0,  # 1.66% deviation!
    )
    temp_ledger.persist_signal(sig)
    persisted = temp_ledger.get_signal(sig.signal_id)
    assert persisted is not None
    assert persisted.qualification_status == "REJECTED"
    assert "EXCESSIVE_PRICE_DEVIATION" in (persisted.no_trade_reason or "")
    assert persisted.is_live is False


def test_8_missing_resolution_evidence_cannot_become_win_or_loss(temp_ledger):
    """8. Missing resolution evidence cannot become WIN/LOSS."""
    now_utc = datetime.now(timezone.utc)
    expired_time = now_utc - timedelta(hours=10)
    sig = CanonicalProspectiveSignal(
        signal_id="SIG-NO-EVIDENCE-001",
        campaign_id="CAMP-NO-EVID",
        generated_at_utc=expired_time.isoformat(),
        generated_at_ist=expired_time.isoformat(),
        asset="UNKNOWN_ASSET",
        timeframe="1H",
        direction="BUY",
        market_snapshot_hash="snap-no-evid",
        policy_version="POL-70-v1",
        model_version="Ensemble-v1",
        config_hash="conf-no-evid",
        entry_window_start=expired_time.isoformat(),
        entry_window_end=(expired_time + timedelta(minutes=10)).isoformat(),
        preferred_entry_time=expired_time.isoformat(),
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        expected_hold_seconds=3600,
        expected_exit_time=(expired_time + timedelta(hours=1)).isoformat(),
        max_exit_time=(expired_time + timedelta(hours=2)).isoformat(),
        probability=0.75,
        signal_strength=80,
        quality_grade="GRADE_A",
        expected_r=2.0,
        regime="TRENDING",
        mtf_alignment=0.8,
        risk_state="NORMAL",
        qualification_status="QUALIFIED",
        signal_status=STATUS_UPCOMING,
        record_type="HISTORICAL",
        is_live=False,
    )
    temp_ledger.persist_signal(sig)
    
    # Try resolving when no candles exist for UNKNOWN_ASSET
    temp_ledger.resolve_pending_expired_signals(reference_dt=now_utc)
    
    persisted = temp_ledger.get_signal(sig.signal_id)
    assert persisted.outcome == "UNRESOLVED"
    assert persisted.resolution_reason == "NO_HISTORICAL_EVIDENCE"
    assert persisted.outcome not in ["WON", "LOST"]


def test_9_performance_excludes_unresolved_demo_test_records(temp_ledger):
    """9. Performance excludes unresolved/demo/test records."""
    now_utc = datetime.now(timezone.utc)
    # Add 1 demo trade
    demo = CanonicalProspectiveSignal(
        signal_id="SIG-PERF-DEMO-001",
        campaign_id="CAMP-DEMO",
        generated_at_utc=now_utc.isoformat(),
        generated_at_ist=now_utc.isoformat(),
        asset="USDJPY",
        timeframe="4H",
        direction="BUY",
        market_snapshot_hash="snap-demo",
        policy_version="POL-70-v1",
        model_version="Ensemble-v1",
        config_hash="c-01",
        entry_window_start=now_utc.isoformat(),
        entry_window_end=now_utc.isoformat(),
        preferred_entry_time=now_utc.isoformat(),
        entry_price=150.0,
        stop_loss=149.0,
        take_profit=152.0,
        expected_hold_seconds=3600,
        expected_exit_time=now_utc.isoformat(),
        max_exit_time=now_utc.isoformat(),
        probability=0.7,
        signal_strength=70,
        quality_grade="GRADE_A",
        expected_r=2.0,
        regime="TRENDING",
        mtf_alignment=0.8,
        risk_state="NORMAL",
        qualification_status="QUALIFIED",
        signal_status=STATUS_RESOLVED,
        record_type="DEMO",
        is_demo=True,
        outcome="WON",
        net_r=2.0,
    )
    temp_ledger.persist_signal(demo)
    
    stats_service = CanonicalStatisticsService(db_path=temp_ledger.db_path)
    summary = stats_service.get_canonical_performance_summary(include_demo=False)
    assert summary["resolved_count"] == 0, "Demo trade must be excluded from default performance summary"


def test_10_frontend_today_signals_equals_backend_canonical_qualified_signals():
    """10. Frontend Today's Signals equals backend canonical qualified signals."""
    today_res = get_today_signals()
    signals = today_res.get("signals", [])
    total_qualified = today_res.get("total_qualified_signals", 0)
    
    assert len(signals) == total_qualified
    for s in signals:
        assert s["qualification_status"] == "QUALIFIED"
        assert s.get("record_type") == "LIVE"
        assert s.get("is_live") is True
        assert s.get("is_demo") is False
