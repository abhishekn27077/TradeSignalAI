"""
Phase 46 — Live Statistical Evidence & Performance Governance API Routes.

Exposes 14 REST endpoints under /api/v1/evidence/live/*:
  - GET /api/v1/evidence/live
  - GET /api/v1/evidence/live/status
  - GET /api/v1/evidence/live/confidence
  - GET /api/v1/evidence/live/baselines
  - GET /api/v1/evidence/live/models
  - GET /api/v1/evidence/live/assets
  - GET /api/v1/evidence/live/regimes
  - GET /api/v1/evidence/live/sessions
  - GET /api/v1/evidence/live/calibration
  - GET /api/v1/evidence/live/costs
  - GET /api/v1/evidence/live/drift
  - GET /api/v1/evidence/live/missed
  - GET /api/v1/evidence/live/failed
  - GET /api/v1/evidence/live/audit
"""
from fastapi import APIRouter
from typing import Dict, Any

from app.analytics.live_edge_validation_engine import live_edge_validation_engine
from app.analytics.edge_drift_engine import edge_drift_engine
from app.analytics.daily_signal_journal import daily_signal_journal
from app.analytics.shadow_validation_engine import shadow_validation_engine

router = APIRouter(prefix="/evidence/live", tags=["Phase 46 — Live Statistical Evidence & Governance"])


@router.get("")
async def get_live_evidence_overview() -> Dict[str, Any]:
    """Returns complete live forward evidence overview."""
    metrics = live_edge_validation_engine.compute_live_metrics()
    gates = live_edge_validation_engine.evaluate_14_point_confirmation_gates()
    cohort_meta = shadow_validation_engine.get_cohort_metadata()

    return {
        "cohort_id": cohort_meta.get("validation_cohort", "PHASE43_SHADOW_V1"),
        "model_version": cohort_meta.get("model_version", "3.2.0-frozen"),
        "edge_classification": gates["classification"],
        "traffic_light": gates["traffic_light"],
        "metrics": metrics,
        "confirmation_gates": gates,
    }


@router.get("/status")
async def get_edge_confirmation_status() -> Dict[str, Any]:
    """Returns the 14-point confirmation gate status for edge verification."""
    return live_edge_validation_engine.evaluate_14_point_confirmation_gates()


@router.get("/confidence")
async def get_confidence_intervals() -> Dict[str, Any]:
    """Returns 10,000-iteration bootstrap confidence intervals and probability of profit."""
    return live_edge_validation_engine.compute_bootstrap_confidence_intervals()


@router.get("/baselines")
async def get_baselines_comparison() -> Dict[str, Any]:
    """Returns comparison against Random, Buy & Hold, Trend, and Momentum baselines."""
    return live_edge_validation_engine.evaluate_baselines_comparison()


@router.get("/models")
async def get_live_model_contribution() -> Dict[str, Any]:
    """Returns live-only model contribution and forward ablation results."""
    return live_edge_validation_engine.evaluate_live_model_contribution()


@router.get("/assets")
async def get_asset_robustness() -> Dict[str, Any]:
    """Returns 9-asset robustness breakdown."""
    robustness = live_edge_validation_engine.evaluate_multi_dimensional_robustness()
    return {"assets": robustness["assets"]}


@router.get("/regimes")
async def get_regime_robustness() -> Dict[str, Any]:
    """Returns 5-market-regime robustness breakdown."""
    robustness = live_edge_validation_engine.evaluate_multi_dimensional_robustness()
    return {"regimes": robustness["regimes"]}


@router.get("/sessions")
async def get_session_robustness() -> Dict[str, Any]:
    """Returns 4-trading-session robustness breakdown."""
    robustness = live_edge_validation_engine.evaluate_multi_dimensional_robustness()
    return {"sessions": robustness["sessions"]}


@router.get("/calibration")
async def get_calibration_buckets() -> Dict[str, Any]:
    """Returns 8-bucket confidence calibration curve, Brier score, and ECE."""
    return live_edge_validation_engine.evaluate_8_bucket_calibration()


@router.get("/costs")
async def get_cost_and_slippage_stress() -> Dict[str, Any]:
    """Returns cost multiplier stress test (1x to 3x) and slippage stress."""
    return live_edge_validation_engine.evaluate_cost_and_slippage_stress()


@router.get("/drift")
async def get_drift_analysis() -> Dict[str, Any]:
    """Returns rolling window metrics, edge drift, and model drift warnings."""
    return {
        "rolling_windows": edge_drift_engine.evaluate_rolling_windows(),
        "edge_drift": edge_drift_engine.detect_edge_drift(),
        "model_drift": edge_drift_engine.detect_model_drift(),
    }


@router.get("/missed")
async def get_missed_trades() -> Dict[str, Any]:
    """Returns MFE/MAE analysis for rejected NO_TRADE forecasts."""
    return daily_signal_journal.get_missed_trades()


@router.get("/failed")
async def get_failed_trades() -> Dict[str, Any]:
    """Returns root cause failure diagnostics for losing trades."""
    return daily_signal_journal.get_failed_trades()


@router.get("/audit")
async def get_statistical_audit() -> Dict[str, Any]:
    """Returns reproducibility parameters, deterministic seed, result hashes, and audit checklist."""
    cohort_meta = shadow_validation_engine.get_cohort_metadata()
    ci = live_edge_validation_engine.compute_bootstrap_confidence_intervals()

    return {
        "reproducibility": {
            "validation_cohort": cohort_meta.get("validation_cohort", "PHASE43_SHADOW_V1"),
            "model_version": cohort_meta.get("model_version", "3.2.0-frozen"),
            "bootstrap_seed": ci.get("bootstrap_seed", 464646),
            "bootstrap_iterations": ci.get("iterations", 10000),
            "result_hash": ci.get("result_hash"),
        },
        "evidence_hierarchy": {
            "tier1_historical": "245,774 bars (Reference only)",
            "tier2_oos": "36,866 bars (Benchmark only)",
            "tier3_live_shadow": "Active forward cohort (Real forward observations)",
            "tier4_real_money": "DISABLED_NOT_APPROVED",
        },
    }
