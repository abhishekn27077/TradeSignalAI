"""
Phase 41 & 42 — Intelligence, Health, Data Windows & Prediction Scorecard API Routes.

Endpoints:
  GET  /api/v1/intelligence/data-health       — Historical candle audit & 10 data lineage sources
  GET  /api/v1/intelligence/model-health      — 11 subsystem live operational health matrix
  GET  /api/v1/intelligence/ablation          — Model contribution & ablation comparisons
  GET  /api/v1/intelligence/signal-diagnostics— 9-asset scan diagnostics & exact rejection reasons
  POST /api/v1/intelligence/walkforward-replay— Run zero-lookahead walk-forward replay on real data
  GET  /api/v1/intelligence/data-windows      — 6 non-overlapping data windows certification
  GET  /api/v1/intelligence/oos-validation    — Out-of-sample test validation & Brier score
  GET  /api/v1/intelligence/forecast-timeline/{asset} — Complete forecast timeline with news catalysts
  GET  /api/v1/intelligence/prediction-scorecard — Today / 7D / 30D / Asset / Model scorecards
  GET  /api/v1/intelligence/event-scenarios   — 28 global economic event scenarios & sensitivities
  POST /api/v1/intelligence/news-update-forecast — Ingest news catalyst & spawn new prediction version
"""
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.logs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/intelligence", tags=["Data Intelligence & Model Health"])


# ── Request Models ──────────────────────────────────────────────────────────

class WalkForwardReplayRequest(BaseModel):
    start_date: str
    end_date: str
    assets: Optional[list[str]] = None
    timeframe: str = "1h"
    step_interval_hours: int = 24
    forecast_horizon_hours: int = 24


class NewsUpdateRequest(BaseModel):
    asset: str
    news_catalyst: dict[str, Any]
    old_forecast: dict[str, Any]
    new_forecast: dict[str, Any]


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/data-health", summary="Dataset & Lineage Health Audit")
async def get_data_health():
    """
    Returns authentic audit metrics for the 245,774+ SQLite candle dataset.
    """
    try:
        from app.analytics.data_health_engine import data_health_engine
        result = data_health_engine.get_data_health()
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Data health error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-health", summary="Subsystems Health Matrix")
async def get_model_health():
    """
    Returns the real-time operational status across all 11 intelligence subsystems:
    LIVE | DEGRADED | STALE | ERROR | DISABLED.
    """
    try:
        from app.analytics.model_health_engine import model_health_engine
        result = model_health_engine.get_health_matrix()
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Model health error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ablation", summary="Model Contribution & Ablation Benchmarks")
async def get_model_ablation(
    sample_limit: int = Query(default=500, le=5000, description="Number of historical candles to sample"),
):
    """
    Returns empirical ablation benchmarks on the real dataset.
    """
    try:
        from app.analytics.ablation_engine import model_ablation_engine
        result = model_ablation_engine.run_ablation_benchmark(sample_limit=sample_limit)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Model ablation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signal-diagnostics", summary="Scan-Level Signal Generation Diagnostics")
async def get_signal_diagnostics():
    """
    Provides scan diagnostics for all 9 core assets with transparent rejection reasons.
    """
    try:
        from app.analytics.signal_diagnostics_engine import signal_diagnostics_engine
        result = await signal_diagnostics_engine.get_diagnostics()
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Signal diagnostics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/walkforward-replay", summary="Real Walk-Forward Replay")
async def run_walkforward_replay(request: WalkForwardReplayRequest):
    """
    Executes walk-forward replay against the real historical SQLite candle dataset.
    """
    try:
        from app.analytics.walk_forward_engine import walk_forward_engine

        start = datetime.fromisoformat(request.start_date).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(request.end_date).replace(tzinfo=timezone.utc)

        result = await walk_forward_engine.run_simulation(
            start_date=start,
            end_date=end,
            assets=request.assets,
            timeframe=request.timeframe,
            step_interval_hours=request.step_interval_hours,
            forecast_horizon_hours=request.forecast_horizon_hours,
        )

        return {
            "success": True,
            "simulation_id": result.get("simulation_id"),
            "start_date": result.get("start_date"),
            "end_date": result.get("end_date"),
            "total_snapshots": result.get("total_snapshots"),
            "performance": result.get("performance"),
            "calibration_matrix": result.get("calibration_matrix"),
            "asset_breakdown": result.get("asset_breakdown"),
            "session_breakdown": result.get("session_breakdown"),
            "regime_breakdown": result.get("regime_breakdown"),
            "sample_snapshots": result.get("snapshots", [])[:15],
        }
    except Exception as e:
        logger.error(f"Walk-forward replay error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Phase 42: Data Windows, Timeline, Scorecard & Scenarios ─────────────────

@router.get("/data-windows", summary="Data Window Certification")
async def get_data_windows():
    """
    Returns strict partition boundaries for all 6 data windows:
    Total, Recent 3-4M, Training (70%), Validation (15%), Test (15% OOS), Live.
    """
    try:
        from app.analytics.data_window_engine import data_window_engine
        result = data_window_engine.get_data_windows_certification()
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Data windows error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/oos-validation", summary="Out-of-Sample Test Validation")
async def get_oos_validation(
    sample_limit: int = Query(default=500, le=2000, description="Sample size for OOS validation"),
):
    """
    Computes Out-of-Sample metrics on TEST_DATA including Brier Score, Precision, Recall, and Drawdowns.
    """
    try:
        from app.analytics.data_window_engine import data_window_engine
        result = data_window_engine.run_out_of_sample_validation(sample_limit=sample_limit)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"OOS validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast-timeline/{asset}", summary="Asset Forecast Timeline")
async def get_asset_forecast_timeline(asset: str):
    """
    Returns the complete chronological prediction timeline for an asset,
    including news catalysts, economic events, and immutable forecast versions.
    """
    try:
        from app.analytics.forecast_timeline_engine import forecast_timeline_engine
        result = forecast_timeline_engine.get_forecast_timeline(asset.upper())
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Forecast timeline error for {asset}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prediction-scorecard", summary="Prediction-to-Reality Scorecard")
async def get_prediction_scorecard():
    """
    Returns objective scorecards comparing predictions against realized future market moves:
    Today's Score, 7D Score, 30D Score, Asset Scores, Model Accuracies.
    """
    try:
        from app.analytics.prediction_reality_engine import prediction_reality_engine
        result = prediction_reality_engine.get_scorecards()
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Prediction scorecard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/event-scenarios", summary="28 Economic Event Scenarios")
async def get_event_scenarios():
    """
    Returns 3-way probabilistic scenarios (HOT, IN_LINE, COOL) and asset sensitivity matrices
    across all 28 global macroeconomic events.
    """
    try:
        from app.market_data.economic_calendar import EVENT_TEMPLATES
        return {
            "success": True,
            "total_events_supported": len(EVENT_TEMPLATES),
            "events": EVENT_TEMPLATES,
        }
    except Exception as e:
        logger.error(f"Event scenarios error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/news-update-forecast", summary="News-Driven Forecast Version Update")
async def post_news_update_forecast(request: NewsUpdateRequest):
    """
    Spawns a new versioned prediction snapshot triggered by a news catalyst.
    Preserves historical forecast immutability.
    """
    try:
        from app.analytics.forecast_timeline_engine import forecast_timeline_engine
        result = forecast_timeline_engine.record_news_catalyst_update(
            asset=request.asset.upper(),
            news_catalyst=request.news_catalyst,
            old_forecast=request.old_forecast,
            new_forecast=request.new_forecast,
        )
        return {"success": True, "versioned_record": result}
    except Exception as e:
        logger.error(f"News update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
