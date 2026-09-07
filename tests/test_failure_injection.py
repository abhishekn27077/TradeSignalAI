"""
tests/test_failure_injection.py
===============================
Adversarial Failure Injection & Fail-Closed Resilience Tests (Phase 72).

Verifies:
1. All 12 simulated failure modes degrade safely without process crash.
2. System never fabricates random signals during feed outage or model downtime.
"""

import pytest
from app.runtime.failure_injector import failure_injector


def test_all_failure_scenarios_pass_fail_closed():
    """All failure scenarios must pass with 100% fail-closed resilience."""
    res = failure_injector.run_all_failure_injections()
    assert res["failed_count"] == 0
    assert res["passed_count"] == res["total_scenarios_tested"]
    assert "FAIL-CLOSED RESILIENT" in res["resilience_verdict"]
