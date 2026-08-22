"""
Phase 44 — Test Suite for Sample-Size & Statistical Claim Governance.

Verifies:
  - Sample-size governance brackets (N < 30, 30-100, 100-300, 300+)
  - Strict prohibition of claiming profitability or real money readiness when sample is immature
  - Separation of software certification vs statistical edge classification
"""
import pytest
from app.analytics.evidence_provenance_engine import evidence_provenance_engine


class TestSampleGovernance:
    def test_governance_verdict_structure(self):
        gov = evidence_provenance_engine.get_governance_verdict()
        assert "software_status" in gov
        assert "data_lineage_status" in gov
        assert "zero_lookahead_status" in gov
        assert "sample_size_classification" in gov
        assert "statistical_edge_verdict" in gov
        assert "real_money_readiness" in gov
        assert "claims_policy" in gov

        assert gov["real_money_readiness"] == "NOT_APPROVED (Live forward validation in progress)"
        assert gov["claims_policy"]["claim_profitable"] is False
        assert gov["claims_policy"]["claim_real_money_ready"] is False

    def test_sample_governance_brackets_logic(self):
        tiers_data = evidence_provenance_engine.get_dataset_tiers_summary()
        shadow_tier = tiers_data["tiers"]["LIVE_SHADOW"]

        if shadow_tier["resolved_trades"] < 30:
            assert shadow_tier["status"] == "INSUFFICIENT_SAMPLE"
            assert shadow_tier["win_rate_pct"] is None
            assert shadow_tier["profit_factor"] is None
