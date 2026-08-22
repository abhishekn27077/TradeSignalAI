"""
Phase 40 — Forecast Intelligence API Routes.

Endpoints:
  GET  /api/v1/forecasts/today       — Live active session forecasts across 9 assets
  GET  /api/v1/forecasts/tomorrow    — Next trading day forecasts with event risks & scenarios
  GET  /api/v1/forecasts/ledger      — Historical prediction ledger with outcomes & P&L
  POST /api/v1/backtest/forecast-replay — Walk-forward simulation with performance stats
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.logs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Forecast Intelligence"])


# ── Request Models ──────────────────────────────────────────────────────────

class ForecastReplayRequest(BaseModel):
    start_date: str  # ISO format
    end_date: str    # ISO format
    assets: Optional[list[str]] = None
    step_interval_hours: int = 24
    forecast_horizon_hours: int = 24


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/forecasts/today", summary="Get Today's Forecasts")
async def get_today_forecasts():
    """
    Get live active session forecasts and consensus across all 9 core assets.
    Each forecast includes multi-model breakdown, confidence, direction,
    and explicit Forecast vs Trade Signal distinction.
    """
    try:
        from app.analytics.tomorrow_forecast_engine import tomorrow_forecast_engine
        result = await tomorrow_forecast_engine.generate_today_forecasts()
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Today's forecasts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecasts/tomorrow", summary="Get Tomorrow's Forecasts")
async def get_tomorrow_forecasts():
    """
    Get next trading day forecasts with event risks, 3-way scenarios,
    multi-model consensus, and AI analysis across all 9 core assets.
    Includes explicit Forecast vs Trade Signal qualification.
    """
    try:
        from app.analytics.tomorrow_forecast_engine import tomorrow_forecast_engine
        result = await tomorrow_forecast_engine.generate_tomorrow_forecasts()
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Tomorrow's forecasts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecasts/ledger", summary="Prediction Ledger")
async def get_prediction_ledger(
    days: int = Query(default=7, le=90, description="Number of days to look back"),
    asset: Optional[str] = Query(default=None, description="Filter by asset"),
):
    """
    Returns the prediction ledger showing historical forecasts,
    predictions made, actual prices, outcome, and P&L.

    Shows original prediction at time of generation (IMMUTABLE),
    with outcome resolution appended after forecast horizon closed.
    """
    try:
        from app.analytics.walk_forward_engine import walk_forward_engine

        now = datetime.now(timezone.utc)
        end = now
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        from datetime import timedelta
        start = start - timedelta(days=days)

        assets = [asset] if asset else None
        result = await walk_forward_engine.run_simulation(
            start_date=start,
            end_date=end,
            assets=assets,
            step_interval_hours=24,
            forecast_horizon_hours=24,
        )

        # Format as ledger entries
        ledger_entries = []
        for snap in result.get("snapshots", []):
            ledger_entries.append({
                "forecast_id": snap.get("forecast_id"),
                "asset": snap.get("asset"),
                "date": snap.get("generated_at", "")[:10],
                "direction": snap.get("direction"),
                "confidence": snap.get("confidence"),
                "entry_price": snap.get("entry_price"),
                "stop_loss": snap.get("stop_loss"),
                "take_profit": snap.get("take_profit"),
                "risk_reward": snap.get("risk_reward_ratio"),
                "outcome": snap.get("outcome"),
                "exit_price": snap.get("exit_price"),
                "net_pnl": snap.get("net_pnl"),
                "r_multiple": snap.get("r_multiple"),
                "directional_correct": snap.get("directional_correct"),
                "is_trade_signal": snap.get("is_trade_signal_qualified", False),
            })

        return {
            "success": True,
            "days": days,
            "total_entries": len(ledger_entries),
            "entries": ledger_entries,
            "performance": result.get("performance", {}),
        }
    except Exception as e:
        logger.error(f"Prediction ledger error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest/forecast-replay", summary="Walk-Forward Forecast Replay")
async def run_forecast_replay(request: ForecastReplayRequest):
    """
    Execute a walk-forward simulation across a historical date range.
    Returns performance stats, confidence calibration table,
    and per-asset breakdown.

    Zero lookahead: at step T, only data <= T is used.
    """
    try:
        from app.analytics.walk_forward_engine import walk_forward_engine

        start = datetime.fromisoformat(request.start_date).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(request.end_date).replace(tzinfo=timezone.utc)

        result = await walk_forward_engine.run_simulation(
            start_date=start,
            end_date=end,
            assets=request.assets,
            step_interval_hours=request.step_interval_hours,
            forecast_horizon_hours=request.forecast_horizon_hours,
        )

        # Return summary without full snapshot list (too large)
        return {
            "success": True,
            "simulation_id": result["simulation_id"],
            "start_date": result["start_date"],
            "end_date": result["end_date"],
            "total_snapshots": result["total_snapshots"],
            "performance": result["performance"],
            "calibration_matrix": result["calibration_matrix"],
            "asset_breakdown": result["asset_breakdown"],
            "sample_snapshots": result["snapshots"][:10],  # First 10 for preview
        }
    except Exception as e:
        logger.error(f"Forecast replay error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
