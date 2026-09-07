"""
tests/test_overfitting_detection.py
===================================
Overfitting & Magic Number Audit Tests (Phase 72).

Verifies:
1. Zero hardcoded magic asset thresholds or date-specific override hacks.
2. Models use canonical feature definitions across all 9 assets.
"""

import pytest
from app.analytics.ablation_engine import ablation_engine


def test_overfitting_audit_scans():
    """Overfitting audit must report zero hardcoded asset overrides."""
    audit = ablation_engine.audit_overfitting()
    assert audit["hardcoded_asset_magic_numbers_found"] == 0
    assert audit["date_specific_override_rules_found"] == 0
    assert audit["lookahead_leakage_violations_found"] == 0
    assert "ROBUST" in audit["parameter_sensitivity_verdict"]
