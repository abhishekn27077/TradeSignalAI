"""
tests/test_phase33_signal_lifecycle.py
Phase 33 — Signal State Machine & Identity Guard tests.
"""
import pytest
import hashlib
from datetime import datetime, timezone

from app.core.signal_state import SignalState, SignalStateMachine, InvalidTransitionError
from app.core.signal_identity import SignalIdentityGuard


# ─── State Machine ────────────────────────────────────────────────────────────

class TestSignalStateMachine:

    def test_initial_state_is_detected(self):
        assert SignalState.DETECTED == "DETECTED"

    def test_valid_transition_detected_to_analyzing(self):
        new = SignalStateMachine.transition(SignalState.DETECTED, "start_analysis")
        assert new == SignalState.ANALYZING

    def test_valid_transition_analyzing_to_approved(self):
        new = SignalStateMachine.transition(SignalState.ANALYZING, "approve")
        assert new == SignalState.APPROVED

    def test_valid_transition_approved_to_active(self):
        new = SignalStateMachine.transition(SignalState.APPROVED, "activate")
        assert new == SignalState.ACTIVE

    def test_valid_transition_active_tp_hit(self):
        new = SignalStateMachine.transition(SignalState.ACTIVE, "tp_hit")
        assert new == SignalState.TP_HIT

    def test_valid_transition_active_sl_hit(self):
        new = SignalStateMachine.transition(SignalState.ACTIVE, "sl_hit")
        assert new == SignalState.SL_HIT

    def test_valid_transition_active_time_exit(self):
        new = SignalStateMachine.transition(SignalState.ACTIVE, "time_exit")
        assert new == SignalState.TIME_EXIT

    def test_valid_transition_active_ambiguous(self):
        new = SignalStateMachine.transition(SignalState.ACTIVE, "ambiguous")
        assert new == SignalState.AMBIGUOUS

    def test_valid_transition_to_completed(self):
        for state in [SignalState.TP_HIT, SignalState.SL_HIT, SignalState.TIME_EXIT, SignalState.AMBIGUOUS]:
            new = SignalStateMachine.transition(state, "complete")
            assert new == SignalState.COMPLETED

    def test_invalid_transition_raises(self):
        with pytest.raises(InvalidTransitionError):
            SignalStateMachine.transition(SignalState.DETECTED, "tp_hit")

    def test_invalid_transition_non_strict_returns_none(self):
        result = SignalStateMachine.transition(SignalState.DETECTED, "tp_hit", strict=False)
        assert result is None

    def test_completed_is_terminal(self):
        assert SignalStateMachine.is_terminal(SignalState.COMPLETED) is True

    def test_rejected_is_terminal(self):
        assert SignalStateMachine.is_terminal(SignalState.REJECTED) is True

    def test_active_is_not_terminal(self):
        assert SignalStateMachine.is_terminal(SignalState.ACTIVE) is False

    def test_tp_hit_is_resolved(self):
        assert SignalStateMachine.is_resolved(SignalState.TP_HIT) is True

    def test_detected_is_not_resolved(self):
        assert SignalStateMachine.is_resolved(SignalState.DETECTED) is False

    def test_string_state_accepted(self):
        new = SignalStateMachine.transition("DETECTED", "start_analysis")
        assert new == SignalState.ANALYZING

    def test_full_tp_lifecycle(self):
        """DETECTED → ANALYZING → APPROVED → ACTIVE → TP_HIT → COMPLETED"""
        s = SignalState.DETECTED
        s = SignalStateMachine.transition(s, "start_analysis")
        assert s == SignalState.ANALYZING
        s = SignalStateMachine.transition(s, "approve")
        assert s == SignalState.APPROVED
        s = SignalStateMachine.transition(s, "activate")
        assert s == SignalState.ACTIVE
        s = SignalStateMachine.transition(s, "tp_hit")
        assert s == SignalState.TP_HIT
        s = SignalStateMachine.transition(s, "complete")
        assert s == SignalState.COMPLETED

    def test_full_sl_lifecycle(self):
        """DETECTED → ANALYZING → WAITING → ACTIVE → SL_HIT → COMPLETED"""
        s = SignalState.DETECTED
        s = SignalStateMachine.transition(s, "start_analysis")
        s = SignalStateMachine.transition(s, "wait")
        assert s == SignalState.WAITING
        s = SignalStateMachine.transition(s, "activate")
        s = SignalStateMachine.transition(s, "sl_hit")
        s = SignalStateMachine.transition(s, "complete")
        assert s == SignalState.COMPLETED

    def test_rejection_lifecycle(self):
        s = SignalStateMachine.transition(SignalState.DETECTED, "reject")
        assert s == SignalState.REJECTED
        assert SignalStateMachine.is_terminal(s) is True


# ─── Signal Identity Guard ────────────────────────────────────────────────────

class TestSignalIdentityGuard:

    def _ts(self):
        return datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)

    def test_hash_is_deterministic(self):
        h1 = SignalIdentityGuard.compute_hash("BTCUSD", "H4", self._ts(), "BUY")
        h2 = SignalIdentityGuard.compute_hash("BTCUSD", "H4", self._ts(), "BUY")
        assert h1 == h2

    def test_hash_length_is_64(self):
        h = SignalIdentityGuard.compute_hash("BTCUSD", "H4", self._ts(), "BUY")
        assert len(h) == 64

    def test_different_direction_produces_different_hash(self):
        h_buy  = SignalIdentityGuard.compute_hash("BTCUSD", "H4", self._ts(), "BUY")
        h_sell = SignalIdentityGuard.compute_hash("BTCUSD", "H4", self._ts(), "SELL")
        assert h_buy != h_sell

    def test_different_symbol_produces_different_hash(self):
        h1 = SignalIdentityGuard.compute_hash("BTCUSD", "H4", self._ts(), "BUY")
        h2 = SignalIdentityGuard.compute_hash("ETHUSD", "H4", self._ts(), "BUY")
        assert h1 != h2

    def test_different_timestamp_produces_different_hash(self):
        ts1 = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)
        ts2 = datetime(2026, 8, 19, 16, 0, 0, tzinfo=timezone.utc)
        h1 = SignalIdentityGuard.compute_hash("BTCUSD", "H4", ts1, "BUY")
        h2 = SignalIdentityGuard.compute_hash("BTCUSD", "H4", ts2, "BUY")
        assert h1 != h2

    def test_case_insensitive_asset(self):
        h1 = SignalIdentityGuard.compute_hash("btcusd", "H4", self._ts(), "buy")
        h2 = SignalIdentityGuard.compute_hash("BTCUSD", "H4", self._ts(), "BUY")
        assert h1 == h2

    def test_string_timestamp_accepted(self):
        h = SignalIdentityGuard.compute_hash(
            "BTCUSD", "H4", "2026-08-19T12:00:00+00:00", "BUY"
        )
        assert len(h) == 64

    def test_build_identity_from_dict(self):
        d = {
            "asset": "EURUSD",
            "timeframe": "H4",
            "candle_timestamp": self._ts(),
            "direction": "SELL",
        }
        h = SignalIdentityGuard.build_identity(d)
        expected = SignalIdentityGuard.compute_hash("EURUSD", "H4", self._ts(), "SELL")
        assert h == expected
