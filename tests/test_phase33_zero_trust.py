"""
tests/test_phase33_zero_trust.py
Phase 33 — Zero-Trust failure mode tests.
Verifies the system degrades gracefully and honestly rather than fabricating data.
"""
import pytest
import pandas as pd
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from app.core.data_freshness import DataFreshnessChecker
from app.core.candle_discipline import CandleDisciplineChecker
from app.core.signal_state import SignalStateMachine, SignalState, InvalidTransitionError
from app.core.signal_identity import SignalIdentityGuard
from app.strategies.risk_engine import RiskEngine, DECISION_NO_TRADE
from app.intelligence.faiss_memory import FAISSMemoryEngine, STATUS_UNAVAILABLE


class TestZeroTrustFailureModes:

    # ── Stale Data ─────────────────────────────────────────────────────────

    def test_stale_data_blocked_h4(self):
        """Data older than 600s for H4 must return DATA_STALE."""
        now = datetime.now(timezone.utc)
        old_ts = (now - timedelta(seconds=700)).isoformat()
        rates = [{"timestamp": old_ts, "close": 100.0}]
        result = DataFreshnessChecker.check("BTCUSD", "H4", rates, provider="test")
        assert result.status == "DATA_STALE"

    def test_empty_rates_returns_unavailable(self):
        result = DataFreshnessChecker.check("BTCUSD", "H4", [], provider="test")
        assert result.status == "UNAVAILABLE"
        assert result.reason == "EMPTY_RATES_RESPONSE"

    def test_missing_timestamp_returns_unavailable(self):
        rates = [{"close": 100.0}]  # no timestamp field
        result = DataFreshnessChecker.check("BTCUSD", "H4", rates, provider="test")
        assert result.status == "UNAVAILABLE"
        assert "MISSING_TIMESTAMP" in result.reason

    def test_fresh_data_accepted(self):
        now = datetime.now(timezone.utc)
        fresh_ts = (now - timedelta(seconds=30)).isoformat()
        rates = [{"timestamp": fresh_ts, "close": 100.0}]
        result = DataFreshnessChecker.check("BTCUSD", "H4", rates, provider="test")
        assert result.status == "FRESH"

    # ── Look-Ahead Bias ────────────────────────────────────────────────────

    def test_future_candle_blocked(self):
        now = datetime.now(timezone.utc)
        idx = pd.date_range(start=now - timedelta(hours=3), periods=5, freq="h", tz="UTC")
        df = pd.DataFrame({"close": range(5)}, index=idx)
        prediction_ts = now - timedelta(hours=2)  # some rows are AFTER prediction
        result = CandleDisciplineChecker.validate(df, prediction_ts)
        assert result.passed is False
        assert result.violating_rows > 0

    # ── Invalid State Transitions ──────────────────────────────────────────

    def test_cannot_skip_from_detected_to_completed(self):
        with pytest.raises(InvalidTransitionError):
            SignalStateMachine.transition(SignalState.DETECTED, "complete")

    def test_cannot_go_from_completed_to_active(self):
        with pytest.raises(InvalidTransitionError):
            SignalStateMachine.transition(SignalState.COMPLETED, "activate")

    def test_cannot_go_from_rejected_to_approved(self):
        with pytest.raises(InvalidTransitionError):
            SignalStateMachine.transition(SignalState.REJECTED, "approve")

    # ── Duplicate Signal Prevention ─────────────────────────────────────────

    def test_same_inputs_produce_same_hash(self):
        ts = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)
        h1 = SignalIdentityGuard.compute_hash("BTCUSD", "H4", ts, "BUY")
        h2 = SignalIdentityGuard.compute_hash("BTCUSD", "H4", ts, "BUY")
        assert h1 == h2

    def test_different_candle_time_produces_different_hash(self):
        ts1 = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)
        ts2 = datetime(2026, 8, 19, 16, 0, 0, tzinfo=timezone.utc)
        h1 = SignalIdentityGuard.compute_hash("BTCUSD", "H4", ts1, "BUY")
        h2 = SignalIdentityGuard.compute_hash("BTCUSD", "H4", ts2, "BUY")
        assert h1 != h2

    # ── Risk Engine Failure Modes ───────────────────────────────────────────

    def test_zero_entry_price_blocked(self):
        engine = RiskEngine()
        df = pd.DataFrame([{"close": 0.0, "ATR_14": 0.0, "RSI_14": 50.0}])
        consensus = engine.calculate_setup(df, {
            "master_signal": "BULLISH",
            "consensus_expected_return": 0.01,
            "agreement_percentage": 70,
            "intelligence": {},
        })
        assert consensus["master_signal"] == DECISION_NO_TRADE
        assert consensus["risk_trace"]["validity"]["entry_valid"] is False

    def test_high_rr_threshold_rejects(self):
        engine = RiskEngine(min_risk_reward=100.0)  # impossible threshold
        df = pd.DataFrame([{"close": 100.0, "ATR_14": 1.0, "RSI_14": 50.0}])
        consensus = engine.calculate_setup(df, {
            "master_signal": "BULLISH",
            "consensus_expected_return": 0.01,
            "agreement_percentage": 70,
            "intelligence": {},
        })
        assert consensus["master_signal"] == DECISION_NO_TRADE

    # ── FAISS Failure Modes ─────────────────────────────────────────────────

    def test_faiss_no_index_returns_unavailable(self):
        engine = FAISSMemoryEngine()
        result = engine.get_historical_analogs(
            "NONEXISTENT", "H4",
            pd.DataFrame(),
            pd.Timestamp("2026-08-19 12:00:00", tz="UTC"),
        )
        assert result["status"] == STATUS_UNAVAILABLE
        assert result["leak_check"] is False

    def test_faiss_empty_df_returns_unavailable(self):
        engine = FAISSMemoryEngine()
        # Pretend index exists but df is empty
        result = engine.get_historical_analogs(
            "BTCUSD", "H1",
            pd.DataFrame(),
            pd.Timestamp("2026-08-19 12:00:00", tz="UTC"),
        )
        assert result["status"] == STATUS_UNAVAILABLE

    # ── Evidence Ledger Gate ────────────────────────────────────────────────

    def test_evidence_ledger_blocks_unresolved_signal(self, tmp_path, monkeypatch):
        from app.execution.evidence_ledger import EvidenceLedger
        import pathlib
        monkeypatch.setattr("app.execution.evidence_ledger.EVIDENCE_DIR", tmp_path)
        monkeypatch.setattr(
            "app.execution.evidence_ledger.SIGNAL_TRACE_FILE",
            tmp_path / "PHASE33_REAL_SIGNAL_TRACE.json"
        )
        ledger = EvidenceLedger()
        result = ledger.write_signal_trace("test-trace-id", {"outcome": "OUTCOME_UNRESOLVED"})
        assert result == "WRITE_BLOCKED_OUTCOME_UNRESOLVED"

    def test_evidence_ledger_allows_resolved_signal(self, tmp_path, monkeypatch):
        from app.execution.evidence_ledger import EvidenceLedger
        monkeypatch.setattr("app.execution.evidence_ledger.EVIDENCE_DIR", tmp_path)
        monkeypatch.setattr(
            "app.execution.evidence_ledger.SIGNAL_TRACE_FILE",
            tmp_path / "PHASE33_REAL_SIGNAL_TRACE.json"
        )
        ledger = EvidenceLedger()
        result = ledger.write_signal_trace("test-trace-id", {
            "outcome": "TP_HIT",
            "net_pnl": 0.75,
        })
        assert "PHASE33_REAL_SIGNAL_TRACE" in result
