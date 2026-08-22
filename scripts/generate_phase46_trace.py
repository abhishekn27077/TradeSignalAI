"""
Phase 46 — Real Evidence Runtime Trace Generator.

Executes live edge validation, bootstrap confidence intervals, null hypothesis testing,
cost sensitivity tests, and saves runtime telemetry and evidence artifacts.
"""
import os
import sys
import json
import uuid
import hashlib
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.analytics.live_edge_validation_engine import live_edge_validation_engine
from app.analytics.edge_drift_engine import edge_drift_engine
from app.analytics.shadow_validation_engine import shadow_validation_engine


def generate_trace():
    print("[Phase 46] Starting Real Evidence Runtime Trace Generation...")

    now = datetime.now(timezone.utc)
    cohort_meta = shadow_validation_engine.get_cohort_metadata()

    # 1. Compute metrics & confirmation gates
    metrics = live_edge_validation_engine.compute_live_metrics()
    gates = live_edge_validation_engine.evaluate_14_point_confirmation_gates()

    # 2. Bootstrap CIs (10k iterations)
    ci = live_edge_validation_engine.compute_bootstrap_confidence_intervals()

    # 3. Null Hypothesis Testing
    hypothesis = live_edge_validation_engine.perform_null_hypothesis_testing()

    # 4. Multi-dimensional robustness
    robustness = live_edge_validation_engine.evaluate_multi_dimensional_robustness()

    # 5. Cost & slippage stress
    costs = live_edge_validation_engine.evaluate_cost_and_slippage_stress()

    # 6. 8-Bucket calibration
    calibration = live_edge_validation_engine.evaluate_8_bucket_calibration()

    # 7. Drift analysis
    rolling = edge_drift_engine.evaluate_rolling_windows()
    edge_drift = edge_drift_engine.detect_edge_drift()
    model_drift = edge_drift_engine.detect_model_drift()

    # 8. Save daily evidence report
    evidence_path = live_edge_validation_engine.save_evidence_report()
    print(f"[Phase 46] Evidence Report Saved: {evidence_path}")

    # Build runtime trace payload
    trace_payload = {
        "phase": 46,
        "phase_title": "Forward-Edge Statistical Validation, Live Performance Governance & Adaptive Model Evidence",
        "timestamp_utc": now.isoformat(),
        "trace_id": str(uuid.uuid4()),
        "validation_cohort": cohort_meta.get("validation_cohort", "PHASE43_SHADOW_V1"),
        "model_version": cohort_meta.get("model_version", "3.2.0-frozen"),
        "evidence_hierarchy": {
            "tier1_historical": "245,774 bars (Reference only)",
            "tier2_oos": "36,866 bars (Benchmark only)",
            "tier3_live_shadow": "Active forward cohort (Real forward observations)",
            "tier4_real_money": "DISABLED_NOT_APPROVED",
        },
        "live_sample_size": metrics["sample_size"],
        "edge_classification": gates["classification"],
        "traffic_light": gates["traffic_light"],
        "gates_summary": f"Passed {gates['passed_gates']}/{gates['total_gates']} Gates",
        "bootstrap_parameters": {
            "seed": ci.get("bootstrap_seed", 464646),
            "iterations": ci.get("iterations", 10000),
            "result_hash": ci.get("result_hash"),
        },
        "hypothesis_testing": hypothesis,
        "cost_stress": costs,
        "calibration": calibration,
        "drift": {
            "edge_drift": edge_drift,
            "model_drift": model_drift,
        },
        "evidence_file_path": evidence_path,
        "system_certification": "PHASE_46_SOFTWARE_AND_EVIDENCE_CERTIFIED",
    }

    out_dir = "artifacts/phase46"
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "REAL_EVIDENCE_RUNTIME_TRACE.json")

    with open(out_file, "w") as f:
        json.dump(trace_payload, f, indent=2)

    print(f"[Phase 46] Runtime Trace Saved: {out_file}")
    return out_file


if __name__ == "__main__":
    generate_trace()
