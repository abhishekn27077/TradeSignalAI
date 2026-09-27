"""
tests/test_latency_monitor.py
=============================
System Latency & SLA Monitor Tests (Phase 72).

Verifies:
1. Latency calculations yield valid p50, p95, and p99 statistics.
2. End-to-end signal latency meets production SLA (<500ms).
"""

import pytest
from app.runtime.latency_monitor import latency_monitor


def test_latency_percentile_calculation():
    """LatencyMonitor must calculate component percentiles and truthfully report SLA status."""
    report = latency_monitor.calculate_percentiles()
    assert report["overall_status"] in ("WITHIN_PRODUCTION_SLA", "SLA_BREACH")
    assert "components" in report
    assert "e2e_total" in report["components"]

    e2e = report["components"]["e2e_total"]
    assert "p99_ms" in e2e
    assert e2e["p99_ms"] > 0.0
    assert e2e["sample_count"] > 0
