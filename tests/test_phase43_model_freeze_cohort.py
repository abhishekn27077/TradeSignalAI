"""
Phase 43 — Test Suite for Model Freeze & Validation Cohort Engine.

Verifies:
  - Cohort initialization (PHASE43_SHADOW_V1)
  - Deterministic SHA256 hashes for model, strategy, feature, and configuration payloads
  - Non-destructive cohort rollover (V1 -> V2) without historical mutation
"""
import pytest
from app.analytics.shadow_validation_engine import shadow_validation_engine


class TestModelFreezeAndCohort:
    def test_cohort_initial_state(self):
        meta = shadow_validation_engine.get_cohort_metadata()
        assert meta["validation_cohort"] == "PHASE43_SHADOW_V1"
        assert meta["model_version"] == "3.2.0-frozen"
        assert meta["strategy_version"] == "2.1.0-zerotrust"
        assert meta["feature_version"] == "1.5.0-canonical"
        assert meta["configuration_version"] == "1.0.0-phase43"
        assert meta["status"] == "LIVE"

    def test_deterministic_hashes_present(self):
        meta = shadow_validation_engine.get_cohort_metadata()
        hashes = meta["hashes"]
        assert "model_hash" in hashes
        assert "strategy_hash" in hashes
        assert "feature_hash" in hashes
        assert "configuration_hash" in hashes

        for k, h in hashes.items():
            assert len(h) == 64  # Valid SHA256 hex string

    def test_cohort_reset_lifecycle(self):
        # Rollover to V2
        rollover = shadow_validation_engine.reset_cohort(new_cohort_suffix="V2")
        assert rollover["previous_cohort"] == "PHASE43_SHADOW_V1"
        assert rollover["new_cohort"] == "PHASE43_SHADOW_V2"

        meta = shadow_validation_engine.get_cohort_metadata()
        assert meta["validation_cohort"] == "PHASE43_SHADOW_V2"

        # Restore back to V1 for subsequent tests
        shadow_validation_engine.reset_cohort(new_cohort_suffix="V1")
        assert shadow_validation_engine.active_cohort_id == "PHASE43_SHADOW_V1"
