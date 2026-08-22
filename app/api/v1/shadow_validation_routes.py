"""
Phase 43 — Shadow Validation & Paper-Trading REST API Routes.

Exposes 18 dedicated endpoints for real-time shadow validation, paper execution,
confidence calibration, statistical significance, and multi-dimensional breakdowns.
"""
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.analytics.shadow_ledger_engine import shadow_ledger_engine
from app.analytics.shadow_statistics_engine import shadow_statistics_engine
from app.analytics.shadow_validation_engine import shadow_validation_engine
from app.logs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/validation/phase43", tags=["Phase 43 Shadow Validation"])


# ── Request Models ──────────────────────────────────────────────────────────

class PauseRequest(BaseModel):
    reason: str = "MANUAL_PAUSE"


class ResetRequest(BaseModel):
    new_cohort_suffix: str = "V2"
    confirmation_key: str = "CONFIRM_COHORT_RESET"


class ReplayRequest(BaseModel):
    start_date: str
    end_date: str
    assets: Optional[list[str]] = None
    timeframe: str = "1h"


# ── Status & Performance Endpoints ──────────────────────────────────────────

@router.get("/status", summary="Live Shadow Validation Status")
async def get_shadow_status():
    """Returns real-time shadow validation cohort status, kill switch state, and engine health."""
    try:
        return {"success": True, **shadow_statistics_engine.get_live_status_summary()}
    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance", summary="Detailed Trading Performance")
async def get_shadow_performance():
    """Returns detailed financial & statistical performance metrics (PF, Expectancy, Max DD, Sharpe, Sortino)."""
    try:
        perf = shadow_statistics_engine.calculate_performance_metrics()
        return {"success": True, "performance": perf}
    except Exception as e:
        logger.error(f"Performance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/paper-trades", summary="All Paper Trades")
async def get_paper_trades(limit: int = Query(default=50, le=500)):
    """Returns historical and active paper trades with realistic transaction cost deductions."""
    try:
        trades = shadow_ledger_engine.get_all_paper_trades(limit=limit)
        return {"success": True, "total_trades": len(trades), "trades": trades}
    except Exception as e:
        logger.error(f"Paper trades error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/open-trades", summary="Open Paper Trades")
async def get_open_trades():
    """Returns currently open paper orders awaiting closed-candle resolution."""
    try:
        trades = shadow_ledger_engine.get_open_paper_trades()
        return {"success": True, "open_trades": trades}
    except Exception as e:
        logger.error(f"Open trades error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calibration", summary="8-Bucket Confidence Calibration")
async def get_shadow_calibration():
    """Returns confidence calibration accuracy, Brier scores, and bucket breakdowns."""
    try:
        cal = shadow_statistics_engine.compute_confidence_calibration()
        return {"success": True, **cal}
    except Exception as e:
        logger.error(f"Calibration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", summary="Bootstrap Statistical Significance")
async def get_shadow_statistics(iterations: int = Query(default=1000, le=5000)):
    """Returns 1,000-iteration bootstrap confidence intervals for expectancy and statistical significance verdict."""
    try:
        stats = shadow_statistics_engine.compute_bootstrap_significance(n_iterations=iterations)
        return {"success": True, **stats}
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Breakdown Endpoints ─────────────────────────────────────────────────────

@router.get("/assets", summary="Asset-by-Asset Breakdown")
async def get_shadow_assets():
    """Returns performance across all 9 core assets and identifies Best & Weakest edge."""
    try:
        return {"success": True, **shadow_statistics_engine.get_asset_breakdown()}
    except Exception as e:
        logger.error(f"Asset breakdown error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regimes", summary="Market Regime Breakdown")
async def get_shadow_regimes():
    """Returns performance segmented across STRONG_BULL, BULL, RANGE, BEAR, and STRONG_BEAR regimes."""
    try:
        return {"success": True, **shadow_statistics_engine.get_regime_breakdown()}
    except Exception as e:
        logger.error(f"Regime breakdown error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", summary="Trading Session Breakdown")
async def get_shadow_sessions():
    """Returns performance segmented by ASIA, LONDON, NEW_YORK, and LONDON_NEW_YORK_OVERLAP."""
    try:
        return {"success": True, **shadow_statistics_engine.get_session_breakdown()}
    except Exception as e:
        logger.error(f"Session breakdown error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events", summary="29 Economic Events Impact Breakdown")
async def get_shadow_events():
    """Returns performance segmented into Pre-event, During-risk-window, and Post-event across all 29 releases."""
    try:
        return {"success": True, **shadow_statistics_engine.get_economic_events_breakdown()}
    except Exception as e:
        logger.error(f"Event breakdown error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news", summary="News Sentiment Impact Breakdown")
async def get_shadow_news():
    """Returns performance segmented by Risk-On/Off mood and positive/negative sentiment."""
    try:
        return {"success": True, **shadow_statistics_engine.get_news_impact_breakdown()}
    except Exception as e:
        logger.error(f"News breakdown error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", summary="Forward Model Contribution / Ablation")
async def get_shadow_models():
    """Returns forward ablation benchmarks on the active validation cohort."""
    try:
        return {"success": True, **shadow_statistics_engine.get_forward_model_contribution()}
    except Exception as e:
        logger.error(f"Model breakdown error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ledger", summary="Immutable Validation Ledger")
async def get_shadow_ledger(limit: int = Query(default=100, le=1000)):
    """Returns immutable prediction snapshots recorded by the forward shadow validator."""
    try:
        preds = shadow_ledger_engine.get_all_predictions(limit=limit)
        return {"success": True, "total_records": len(preds), "records": preds}
    except Exception as e:
        logger.error(f"Ledger error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Control & Replay Endpoints ──────────────────────────────────────────────

@router.post("/start", summary="Start Validation Engine")
async def start_validation():
    """Starts/resumes live shadow validation."""
    try:
        res = shadow_validation_engine.resume_validation()
        return {"success": True, **res}
    except Exception as e:
        logger.error(f"Start validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pause", summary="Pause Validation Engine")
async def pause_validation(req: PauseRequest):
    """Pauses paper trading while keeping forecasting active."""
    try:
        res = shadow_validation_engine.pause_validation(reason=req.reason)
        return {"success": True, **res}
    except Exception as e:
        logger.error(f"Pause validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume", summary="Resume Validation Engine")
async def resume_validation():
    """Resumes paper trading after manual inspection."""
    try:
        res = shadow_validation_engine.resume_validation()
        return {"success": True, **res}
    except Exception as e:
        logger.error(f"Resume validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset", summary="Spawn New Validation Cohort (Non-destructive)")
async def reset_validation(req: ResetRequest):
    """Spawns a new cohort without modifying or deleting past cohort records."""
    if req.confirmation_key != "CONFIRM_COHORT_RESET":
        raise HTTPException(status_code=400, detail="Invalid confirmation key for cohort reset")
    try:
        res = shadow_validation_engine.reset_cohort(new_cohort_suffix=req.new_cohort_suffix)
        return {"success": True, **res}
    except Exception as e:
        logger.error(f"Reset validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/replay", summary="Controlled Historical Replay")
async def replay_validation(req: ReplayRequest):
    """Runs a zero-lookahead chronological replay against historical closed candles."""
    try:
        from app.analytics.walk_forward_engine import walk_forward_engine
        from datetime import datetime, timezone

        start = datetime.fromisoformat(req.start_date).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(req.end_date).replace(tzinfo=timezone.utc)

        sim_res = await walk_forward_engine.run_simulation(
            start_date=start,
            end_date=end,
            assets=req.assets,
            timeframe=req.timeframe,
        )
        return {"success": True, "replay_id": sim_res.get("simulation_id"), "performance": sim_res.get("performance")}
    except Exception as e:
        logger.error(f"Replay error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
