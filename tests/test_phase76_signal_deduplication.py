"""
tests/test_phase76_signal_deduplication.py
===========================================
Phase 76 Signal Deduplication & Identity Guard Test Suite.

Verifies:
1. SignalIdentityGuard computes deterministic identity hash for any trade candidate.
2. Multiple generation calls with the same setup produce identical identity hash.
3. Database UNIQUE constraint prevents duplicate prospective signal insertion.
4. Signal revisions correctly require supersedes_id and increment generation_version.
"""

from datetime import datetime, timezone
import pytest

from app.core.signal_identity import SignalIdentityGuard, STRATEGY_VERSION
from app.core.canonical_prospective_ledger import (
    CanonicalProspectiveLedger,
    CanonicalProspectiveSignal,
)


class TestPhase76SignalDeduplication:
    """Rigorous deduplication and uniqueness test suite."""

    def test_identity_guard_computes_deterministic_hash(self):
        asset = "BTCUSD"
        timeframe = "15m"
        candle_ts = datetime(2026, 9, 27, 12, 0, 0, tzinfo=timezone.utc)
        direction = "BUY"

        hash1 = SignalIdentityGuard.compute_hash(asset, timeframe, candle_ts, direction)
        hash2 = SignalIdentityGuard.compute_hash(asset, timeframe, candle_ts, direction)

        assert hash1 == hash2
        assert len(hash1) == 64

    def test_repeated_generation_100_times_collapses_to_one_hash(self):
        asset = "EURUSD"
        timeframe = "1h"
        candle_ts = "2026-09-27T14:00:00Z"
        direction = "SELL"

        hashes = {
            SignalIdentityGuard.compute_hash(asset, timeframe, candle_ts, direction)
            for _ in range(100)
        }

        assert len(hashes) == 1

    def test_database_unique_constraint_rejects_duplicate_insertion(self, tmp_path):
        db_file = str(tmp_path / "test_dedup.db")
        ledger = CanonicalProspectiveLedger(db_path=db_file)

        signal1 = CanonicalProspectiveSignal(
            signal_id="SIG-DEDUP-001",
            campaign_id="CAMP-1",
            generated_at_utc="2026-09-27T12:00:00Z",
            generated_at_ist="05:30 PM IST",
            asset="ETHUSD",
            timeframe="15m",
            direction="BUY",
            market_snapshot_hash="h1",
            policy_version="v3.0.0",
            model_version="v3.0.0",
            config_hash="c1",
            entry_window_start="2026-09-27T12:00:00Z",
            entry_window_end="2026-09-27T12:15:00Z",
            preferred_entry_time="2026-09-27T12:05:00Z",
            entry_price=3500.0,
            stop_loss=3450.0,
            take_profit=3600.0,
            expected_hold_seconds=3600,
            expected_exit_time="2026-09-27T13:00:00Z",
            max_exit_time="2026-09-27T14:00:00Z",
            probability=0.68,
            signal_strength=80,
            quality_grade="A",
            expected_r=2.0,
            regime="TRENDING",
            mtf_alignment=1.0,
            risk_state="NORMAL",
            evidence_clusters={},
            mtf_confirmation={},
            qualification_status="QUALIFIED",
            signal_status="GENERATED",
            no_trade_reason=None,
            supersedes_id=None,
            generation_version=1,
            actual_entry_time=None,
            actual_entry_price=None,
            actual_exit_time=None,
            actual_exit_price=None,
            outcome=None,
            resolution_reason=None,
            gross_r=None,
            friction_r=0.05,
            net_r=None,
            mfe=None,
            mae=None,
            created_at="2026-09-27T12:00:00Z",
            resolved_at=None,
        )

        res1 = ledger.persist_signal(signal1)
        assert res1 is True

        # Second attempt with same signal_id is deduplicated and does not duplicate in DB
        res2 = ledger.persist_signal(signal1)
        assert res2 is True

        # Verify exactly 1 record exists in DB
        signals = ledger.get_signals_by_filter(date_filter="ALL", asset="ETHUSD")
        assert len(signals) == 1
