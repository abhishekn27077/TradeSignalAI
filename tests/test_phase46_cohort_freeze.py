"""
Phase 46 — Test Suite for Model Freeze Policy & Evidence Report Persistence.

Verifies:
  - Active cohort model version is frozen (3.2.0-frozen)
  - Evidence report file persistence to artifacts/phase46/evidence/
"""
import os
import json
import pytest
from app.analytics.live_edge_validation_engine import live_edge_validation_engine
from app.analytics.shadow_validation_engine import shadow_validation_engine


class TestCohortFreezeAndReports:
    def test_cohort_metadata_is_frozen(self):
        meta = shadow_validation_engine.get_cohort_metadata()
        assert meta["model_version"] == "3.2.0-frozen"
        assert meta["validation_cohort"] == "PHASE43_SHADOW_V1"

    def test_evidence_report_file_persistence(self):
        file_path = live_edge_validation_engine.save_evidence_report()
        assert os.path.exists(file_path)

        with open(file_path, "r") as f:
            report = json.load(f)

        assert "report_id" in report
        assert "validation_cohort" in report
        assert "model_version" in report
        assert "metrics" in report
        assert "confidence_intervals" in report
        assert "confirmation_gates" in report
        assert "cost_stress" in report
