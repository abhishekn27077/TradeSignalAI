"""
app/api/v1/campaign_routes.py
=============================
REST API Endpoints for Prospective Evidence Campaigns & Virtual Paper Portfolio in TradeSignalAI-v3 (Phase 68).
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, Any, Optional
from app.runtime.prospective_campaign_engine import prospective_campaign_engine
from app.core.signal_frequency_controller import signal_frequency_controller
from app.analytics.paper_portfolio_engine import paper_portfolio_engine
from app.analytics.calibration_robustness_engine import calibration_robustness_engine
from app.analytics.daily_evidence_sealer import daily_evidence_sealer
from app.analytics.prospective_performance_engine import prospective_performance_engine

router = APIRouter(prefix="/campaigns", tags=["Prospective Campaigns & Paper Portfolio"])


@router.get("/current")
async def get_current_active_campaign() -> Dict[str, Any]:
    """Retrieves metadata of the currently active prospective evidence campaign."""
    camp = prospective_campaign_engine.get_active_campaign()
    if not camp:
        return {"success": True, "active": False, "campaign": None, "message": "No active campaign currently running."}
    return {"success": True, "active": True, "campaign": camp.to_dict()}


@router.post("/start")
async def start_new_campaign(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Starts or creates a new prospective evidence collection campaign."""
    name = payload.get("name", "Continuous Prospective Validation Campaign")
    policy_version = payload.get("policy_version", "POLICY-68.0.0")
    model_version = payload.get("model_version", "ENSEMBLE-8M-CANONICAL")
    objective = payload.get("objective", "Continuous out-of-sample forward prospective signal evaluation")

    camp = prospective_campaign_engine.create_campaign(name, policy_version, model_version, objective)
    started = prospective_campaign_engine.start_campaign(camp.campaign_id)
    return {"success": True, "campaign": started.to_dict()}


@router.post("/pause")
async def pause_active_campaign(payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    """Pauses signal generation for the active campaign."""
    camp = prospective_campaign_engine.get_active_campaign()
    if not camp:
        raise HTTPException(status_code=400, detail="No active campaign found to pause.")
    reason = payload.get("reason", "USER_REQUESTED")
    paused = prospective_campaign_engine.pause_campaign(camp.campaign_id, reason=reason)
    return {"success": True, "campaign": paused.to_dict()}


@router.post("/resume")
async def resume_campaign(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Resumes a paused campaign."""
    campaign_id = payload.get("campaign_id")
    if not campaign_id:
        raise HTTPException(status_code=400, detail="campaign_id is required.")
    resumed = prospective_campaign_engine.resume_campaign(campaign_id)
    return {"success": True, "campaign": resumed.to_dict()}


@router.get("/{campaign_id}")
async def get_campaign_by_id(campaign_id: str) -> Dict[str, Any]:
    """Returns campaign record by campaign ID."""
    camp = prospective_campaign_engine.get_campaign(campaign_id)
    if not camp:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found.")
    return {"success": True, "campaign": camp.to_dict()}


@router.get("/{campaign_id}/performance")
async def get_campaign_performance(campaign_id: str) -> Dict[str, Any]:
    """Returns multi-window empirical performance for the campaign."""
    camp = prospective_campaign_engine.get_campaign(campaign_id)
    if not camp:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found.")
    perf = prospective_performance_engine.compute_window_performance("30D")
    return {"success": True, "campaign_id": campaign_id, "performance": perf.to_dict()}


@router.get("/{campaign_id}/calibration")
async def get_campaign_calibration(campaign_id: str) -> Dict[str, Any]:
    """Returns 9-bucket probability calibration and signal strength monotonicity metrics."""
    buckets = calibration_robustness_engine.compute_granular_calibration_buckets()
    monotonicity = calibration_robustness_engine.verify_signal_strength_monotonicity()
    grade_sep = calibration_robustness_engine.validate_quality_grade_separation()
    return {
        "success": True,
        "campaign_id": campaign_id,
        "calibration_buckets": buckets,
        "signal_strength_monotonicity": monotonicity,
        "quality_grade_separation": grade_sep,
    }


@router.get("/{campaign_id}/drift")
async def get_campaign_drift(campaign_id: str) -> Dict[str, Any]:
    """Returns multi-metric continuous drift diagnostics."""
    drift = prospective_performance_engine.evaluate_continuous_drift()
    return {"success": True, "campaign_id": campaign_id, "drift": drift.to_dict()}


@router.get("/{campaign_id}/exposure")
async def get_campaign_cluster_exposure(campaign_id: str) -> Dict[str, Any]:
    """Returns correlation cluster exposure across USD FX, Crypto, Metals, and Indices."""
    portfolio_state = paper_portfolio_engine.get_portfolio_state()
    active_positions = portfolio_state.get("open_positions", [])
    exposure = signal_frequency_controller.analyze_cluster_exposure(active_positions)
    return {"success": True, "campaign_id": campaign_id, "exposure": exposure.to_dict()}


@router.get("/{campaign_id}/equity")
async def get_campaign_paper_equity(campaign_id: str) -> Dict[str, Any]:
    """Returns virtual paper portfolio equity curve and risk metrics ($100k starting)."""
    state = paper_portfolio_engine.get_portfolio_state()
    return {"success": True, "campaign_id": campaign_id, "portfolio": state}


@router.get("/{campaign_id}/reports/weekly")
async def get_weekly_evidence_report(campaign_id: str) -> Dict[str, Any]:
    """Generates weekly prospective evidence report with delta comparisons."""
    rep = daily_evidence_sealer.generate_weekly_evidence_report()
    return {"success": True, "campaign_id": campaign_id, "weekly_report": rep}


@router.get("/{campaign_id}/reports/monthly")
async def get_monthly_evidence_report(campaign_id: str) -> Dict[str, Any]:
    """Generates monthly prospective evidence report."""
    rep = daily_evidence_sealer.generate_monthly_evidence_report()
    return {"success": True, "campaign_id": campaign_id, "monthly_report": rep}
