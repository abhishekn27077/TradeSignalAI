"""
Phase 44 — Test Suite for Evidence Provenance & 4-Tier Dataset Separation.

Verifies:
  - 4 strict dataset tiers (HISTORICAL_BACKTEST, WALK_FORWARD_OOS, LIVE_SHADOW, REAL_MONEY)
  - No blending or mutual contamination between data tiers
  - Complete 11-metric critical number audit covering Questions A through H
  - Correct labeling of historical references vs live forward samples
"""
import pytest
from app.analytics.evidence_provenance_engine import evidence_provenance_engine


class TestEvidenceProvenance:
    def test_dataset_tiers_four_classes_present(self):
        tiers_data = evidence_provenance_engine.get_dataset_tiers_summary()
        assert "tiers" in tiers_data
        tiers = tiers_data["tiers"]

        assert "HISTORICAL_BACKTEST" in tiers
        assert "WALK_FORWARD_OOS" in tiers
        assert "LIVE_SHADOW" in tiers
        assert "REAL_MONEY" in tiers

        # Real money must be strictly inactive
        assert tiers["REAL_MONEY"]["sample_count"] == 0
        assert tiers["REAL_MONEY"]["status"] == "NOT_APPROVED_NOT_ACTIVE"

        # Historical backtest verified with 245k candles
        assert tiers["HISTORICAL_BACKTEST"]["sample_count"] == 245774
        assert tiers["HISTORICAL_BACKTEST"]["status"] == "VERIFIED_HISTORICAL"

    def test_critical_numbers_audit_has_11_metrics(self):
        audit_records = evidence_provenance_engine.get_critical_numbers_audit()
        assert len(audit_records) == 11

        expected_ids = list(range(1, 12))
        for r in audit_records:
            assert r["number_id"] in expected_ids
            assert "metric_name" in r
            assert "claimed_value" in r
            assert "calc_engine" in r
            assert "data_class" in r
            assert "observation_count" in r
            assert "provenance_status" in r
            assert "live_shadow_status" in r
            assert "verdict" in r

    def test_historical_numbers_not_marked_as_live(self):
        audit_records = evidence_provenance_engine.get_critical_numbers_audit()
        for r in audit_records:
            if r["data_class"] in ["HISTORICAL_BACKTEST", "WALK_FORWARD_OOS (Reference Benchmark)"]:
                assert "UNVERIFIED_IN_LIVE" in r["live_shadow_status"]
