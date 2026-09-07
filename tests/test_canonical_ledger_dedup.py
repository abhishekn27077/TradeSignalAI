"""
tests/test_canonical_ledger_dedup.py
====================================
Verifies deterministic signal identity, strict ledger deduplication,
unique constraints, and revisioning in the canonical prospective signal ledger (Phase 70).
"""

import pytest
import sqlite3
import os
from datetime import datetime, timezone, timedelta
from app.core.canonical_prospective_ledger import (
    CanonicalProspectiveLedger,
    CanonicalProspectiveSignal,
    STATUS_UPCOMING,
    STATUS_RESOLVED,
    STATUS_SUPERSEDED,
)


@pytest.fixture
def temp_ledger(tmp_path):
    db_file = str(tmp_path / "test_dedup.db")
    ledger = CanonicalProspectiveLedger(db_path=db_file)
    return ledger


def test_deterministic_signal_id_generation(temp_ledger):
    dt = datetime(2026, 8, 26, 12, 0, 0, tzinfo=timezone.utc)
    sig_id_1 = temp_ledger.generate_signal_id("EURUSD", "1H", dt, policy_version="POL-70-v1", generation_version=1)
    sig_id_2 = temp_ledger.generate_signal_id("EURUSD", "1H", dt, policy_version="POL-70-v1", generation_version=1)
    
    assert sig_id_1 == sig_id_2
    assert "EURUSD" in sig_id_1
    assert "1H" in sig_id_1
    assert "20260826-120000" in sig_id_1
    assert "v1" in sig_id_1


def test_duplicate_signal_insertion_prevented(temp_ledger):
    dt = datetime(2026, 8, 26, 12, 0, 0, tzinfo=timezone.utc)
    sig_id = temp_ledger.generate_signal_id("EURUSD", "1H", dt)
    timing = temp_ledger.compute_exact_timing(dt, "1H")

    sig = CanonicalProspectiveSignal(
        signal_id=sig_id,
        campaign_id="CAMP-2026",
        generated_at_utc=dt.isoformat(),
        generated_at_ist="2026-08-26T17:30:00+05:30",
        asset="EURUSD",
        timeframe="1H",
        direction="BUY",
        market_snapshot_hash="hash-123",
        policy_version="POL-70-v1",
        model_version="MODEL-70",
        config_hash="cfg-70",
        entry_window_start=timing["entry_window_start"],
        entry_window_end=timing["entry_window_end"],
        preferred_entry_time=timing["preferred_entry_time"],
        entry_price=1.0850,
        stop_loss=1.0800,
        take_profit=1.0950,
        expected_hold_seconds=3600,
        expected_exit_time=timing["expected_exit_time"],
        max_exit_time=timing["max_exit_time"],
        probability=0.75,
        signal_strength=80,
        quality_grade="A",
        expected_r=0.55,
        regime="TRENDING_BULLISH",
        mtf_alignment=0.85,
        risk_state="NORMAL",
    )

    # First persistence must succeed
    res1 = temp_ledger.persist_signal(sig)
    assert res1 is True

    # Second persistence of exact same signal must be deduplicated
    res2 = temp_ledger.persist_signal(sig)
    assert res2 is True

    # Query count - must be exactly 1
    signals = temp_ledger.get_signals_by_filter(date_filter="ALL", asset="EURUSD")
    assert len(signals) == 1


def test_signal_revisioning_with_supersedes_id(temp_ledger):
    dt = datetime(2026, 8, 26, 12, 0, 0, tzinfo=timezone.utc)
    sig_id_v1 = temp_ledger.generate_signal_id("USDJPY", "4H", dt, generation_version=1)
    timing = temp_ledger.compute_exact_timing(dt, "4H")

    sig_v1 = CanonicalProspectiveSignal(
        signal_id=sig_id_v1,
        campaign_id="CAMP-2026",
        generated_at_utc=dt.isoformat(),
        generated_at_ist="2026-08-26T17:30:00+05:30",
        asset="USDJPY",
        timeframe="4H",
        direction="BUY",
        market_snapshot_hash="hash-123",
        policy_version="POL-70-v1",
        model_version="MODEL-70",
        config_hash="cfg-70",
        entry_window_start=timing["entry_window_start"],
        entry_window_end=timing["entry_window_end"],
        preferred_entry_time=timing["preferred_entry_time"],
        entry_price=152.00,
        stop_loss=151.00,
        take_profit=154.00,
        expected_hold_seconds=14400,
        expected_exit_time=timing["expected_exit_time"],
        max_exit_time=timing["max_exit_time"],
        probability=0.72,
        signal_strength=75,
        quality_grade="A",
        expected_r=0.50,
        regime="TRENDING_BULLISH",
        mtf_alignment=0.80,
        risk_state="NORMAL",
        generation_version=1,
    )
    temp_ledger.persist_signal(sig_v1)

    # Now revise signal to v2 (e.g. higher probability upon candle update)
    sig_id_v2 = temp_ledger.generate_signal_id("USDJPY", "4H", dt, generation_version=2)
    sig_v2 = CanonicalProspectiveSignal(
        signal_id=sig_id_v2,
        campaign_id="CAMP-2026",
        generated_at_utc=dt.isoformat(),
        generated_at_ist="2026-08-26T17:30:00+05:30",
        asset="USDJPY",
        timeframe="4H",
        direction="BUY",
        market_snapshot_hash="hash-456",
        policy_version="POL-70-v1",
        model_version="MODEL-70",
        config_hash="cfg-70",
        entry_window_start=timing["entry_window_start"],
        entry_window_end=timing["entry_window_end"],
        preferred_entry_time=timing["preferred_entry_time"],
        entry_price=152.10,
        stop_loss=151.10,
        take_profit=154.10,
        expected_hold_seconds=14400,
        expected_exit_time=timing["expected_exit_time"],
        max_exit_time=timing["max_exit_time"],
        probability=0.79,
        signal_strength=85,
        quality_grade="A+",
        expected_r=0.65,
        regime="TRENDING_BULLISH",
        mtf_alignment=0.90,
        risk_state="NORMAL",
        supersedes_id=sig_id_v1,
        generation_version=2,
    )
    temp_ledger.persist_signal(sig_v2, allow_revision=True, supersedes_id=sig_id_v1)

    # Fetch active signals (must only return the latest active v2, v1 is superseded)
    active = temp_ledger.get_signals_by_filter(date_filter="ALL", asset="USDJPY")
    assert len(active) == 1
    assert active[0].signal_id == sig_id_v2
    assert active[0].generation_version == 2
    assert active[0].supersedes_id == sig_id_v1
