"""
Phase 44 — Test Suite for SQLite Database Integrity & Pipeline Trace.

Verifies:
  - Total candles in database >= 245,000
  - Zero duplicate predictions in database
  - Zero missing hashes
  - Live shadow pipeline trace execution and output format
"""
import pytest
from app.analytics.reality_audit_engine import reality_audit_engine


class TestDatabaseIntegrity:
    def test_database_integrity_audit(self):
        audit = reality_audit_engine.audit_database_integrity()
        assert "total_candles" in audit
        assert audit["total_candles"] >= 245000
        assert audit["duplicate_predictions"] == 0
        assert audit["orphan_outcomes"] == 0
        assert audit["missing_hashes"] == 0
        assert audit["impossible_timestamps"] == 0
        assert audit["integrity_score_pct"] == 100.0
        assert audit["status"] in ["PASS_CLEAN", "HEALTHY_FALLBACK"]

    def test_execute_live_pipeline_audit_trace(self):
        trace_res = reality_audit_engine.execute_live_pipeline_audit()
        assert trace_res["total_assets_audited"] == 9
        assert len(trace_res["traces"]) == 9

        for t in trace_res["traces"]:
            assert "trace_id" in t
            assert "prediction_id" in t
            assert "asset" in t
            assert "candle_timestamp" in t
            assert "input_hash" in t
            assert "prediction_hash" in t
            assert "decision" in t
            assert t["decision"] in ["TAKE_TRADE", "NO_TRADE"]
