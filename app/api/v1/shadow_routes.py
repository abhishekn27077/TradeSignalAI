"""
app/api/v1/shadow_routes.py
===========================
Shadow-Live Observability & Diagnostic REST Endpoints (Phase 72).

Endpoints:
- [ /shadow/live ] : Real-time active shadow signals, market status, and data freshness.
- [ /shadow/predictions ] : Query immutable prediction snapshots with SHA-256 hashes.
- [ /shadow/performance ] : 30D / 60D / 90D shadow execution performance metrics.
- [ /shadow/drift ] : Real-time model and feature drift status.
- [ /shadow/counterfactual ] : NO_TRADE counterfactual analysis and capital preservation.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Query

from app.shadow.shadow_live_engine import shadow_live_engine
from app.core.market_clock import MarketClock
from app.analytics.edge_drift_engine import edge_drift_engine
from app.analytics.calibration_engine import calibration_engine
from app.analytics.no_trade_engine import no_trade_engine
from app.validation.walk_forward_engine import walk_forward_engine

router = APIRouter(prefix="/shadow", tags=["Shadow-Live Trading"])


@router.get("/live", summary="Get Real-Time Shadow-Live Dashboard State")
def get_shadow_live_state():
    """
    Returns active market state, sessions, data freshness, active signals, and paper orders.
    """
    session_info = MarketClock.get_market_session("EURUSD")
    drift_info = edge_drift_engine.evaluate_system_drift()
    preds = shadow_live_engine.get_predictions(limit=10)

    return {
        "success": True,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "market_session": session_info,
        "drift_status": drift_info.get("drift_status", "NORMAL"),
        "risk_multiplier": drift_info.get("risk_multiplier", 1.0),
        "active_predictions_count": len([p for p in preds if p.get("status") in ["PENDING", "PAPER_ENTERED"]]),
        "recent_predictions": preds,
    }


@router.get("/predictions", summary="Query Immutable Shadow Prediction Snapshots")
def get_shadow_predictions(
    status: Optional[str] = Query("ALL", description="Filter by status (PENDING, WON, LOST, EXPIRED, ALL)"),
    asset: Optional[str] = Query("ALL", description="Filter by symbol"),
    limit: int = Query(50, ge=1, le=500)
):
    """
    Returns point-in-time immutable predictions with SHA-256 snapshot hashes.
    """
    preds = shadow_live_engine.get_predictions(status=status, asset=asset, limit=limit)
    return {
        "success": True,
        "count": len(preds),
        "predictions": preds,
    }


@router.get("/performance", summary="Get Multi-Horizon Shadow Performance")
def get_shadow_performance():
    """
    Returns 30D, 60D, and 90D walk-forward and shadow performance summaries.
    """
    horizons = walk_forward_engine.run_multi_horizon_evaluations()
    calib = calibration_engine.evaluate_calibration()

    return {
        "success": True,
        "evaluation_horizons": horizons,
        "calibration": calib,
    }


@router.get("/drift", summary="Get Model & Feature Drift Diagnostics")
def get_drift_diagnostics():
    """
    Returns real-time feature distribution, directional skew, and performance drift.
    """
    return edge_drift_engine.evaluate_system_drift()


@router.get("/counterfactual", summary="Get NO_TRADE & Counterfactual Metrics")
def get_counterfactual_metrics():
    """
    Returns efficacy of NO_TRADE decisions and counterfactual PnL preserved.
    """
    return no_trade_engine.evaluate_no_trade_effectiveness()
