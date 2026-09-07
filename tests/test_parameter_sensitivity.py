"""
tests/test_parameter_sensitivity.py
===================================
Parameter Sensitivity & Perturbation Robustness Tests (Phase 72).

Verifies:
1. Small perturbations (+-5%, +-10%, +-20%) in indicator thresholds do not cause cliff-edge collapse.
2. System is certified ROBUST against reasonable parameter variations.
"""

import pytest
from app.analytics.ablation_engine import ablation_engine


def test_parameter_sensitivity_perturbations():
    """Ablation engine must confirm robustness across perturbed parameters."""
    res = ablation_engine.run_parameter_sensitivity_test()
    assert res["robustness_score_pct"] >= 90.0
    assert len(res["perturbations"]) > 0
    for p in res["perturbations"]:
        assert p["verdict"] in ["ROBUST", "BASELINE"]
