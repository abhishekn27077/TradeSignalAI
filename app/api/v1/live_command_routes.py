"""
Phase 58.5 — Canonical Live Daily Command Center & Evidence Journal API Routes.

Exposes REST endpoints:
  - GET /api/v1/live/today
  - GET /api/v1/live/yesterday
  - GET /api/v1/live/tomorrow
  - GET /api/v1/live/open
  - GET /api/v1/live/results
  - GET /api/v1/live/models
  - GET /api/v1/live/missed-trades
  - GET /api/v1/live/failed-trades
  - GET /api/v1/live/daily-review
  - GET /api/v1/live/status
"""
from fastapi import APIRouter
from typing import Dict, Any

from app.core.canonical_signal_service import canonical_signal_service
from app.analytics.daily_signal_journal import daily_signal_journal
from app.runtime.live_forecast_scheduler import live_forecast_scheduler
from app.runtime.shadow_outcome_worker import shadow_outcome_worker
from app.analytics.shadow_ledger_engine import shadow_ledger_engine
from app.analytics.shadow_validation_engine import shadow_validation_engine

router = APIRouter(prefix="/live", tags=["Phase 58.5 — Canonical Live Daily Command Center"])


@router.get("/today")
async def get_today_journal() -> Dict[str, Any]:
    """Returns today's signal journal with real-time forecasts, decisions, and rejection reasons."""
    return canonical_signal_service.get_today_journal()


@router.get("/yesterday")
async def get_yesterday_journal() -> Dict[str, Any]:
    """Returns yesterday's predictions paired with realized outcomes, gross/net R, and costs."""
    return daily_signal_journal.get_yesterday_journal()


@router.get("/tomorrow")
async def get_tomorrow_forecasts() -> Dict[str, Any]:
    """Returns dedicated tomorrow forward projections for all 9 assets with AI explanations."""
    return daily_signal_journal.get_tomorrow_forecasts()


@router.get("/open")
async def get_open_shadow_trades() -> Dict[str, Any]:
    """Returns currently open paper trades in the shadow ledger."""
    open_trades = shadow_ledger_engine.get_open_paper_trades()
    return {
        "count": len(open_trades),
        "open_trades": open_trades,
    }


@router.get("/results")
async def get_shadow_results() -> Dict[str, Any]:
    """Returns all resolved paper trade results with complete cost math."""
    all_trades = shadow_ledger_engine._paper_trades
    resolved = [t for t in all_trades if t["status"] in ["TP_HIT", "SL_HIT", "TIME_EXIT", "AMBIGUOUS"]]
    return {
        "total_resolved": len(resolved),
        "wins": sum(1 for t in resolved if t.get("status") == "TP_HIT"),
        "losses": sum(1 for t in resolved if t.get("status") == "SL_HIT"),
        "net_r": round(sum(t.get("net_r", 0.0) for t in resolved), 2),
        "results": resolved,
    }


@router.get("/models")
async def get_model_scorecard() -> Dict[str, Any]:
    """Returns directional accuracy, Brier scores, calibration, and ablation contributions per model."""
    return daily_signal_journal.get_model_scorecard()


@router.get("/missed-trades")
async def get_missed_trades() -> Dict[str, Any]:
    """Returns MFE/MAE analysis for rejected NO_TRADE forecasts."""
    return daily_signal_journal.get_missed_trades()


@router.get("/failed-trades")
async def get_failed_trades() -> Dict[str, Any]:
    """Returns root cause failure diagnostics for losing trades."""
    return daily_signal_journal.get_failed_trades()


@router.get("/daily-review")
async def get_daily_review() -> Dict[str, Any]:
    """Returns the automated end-of-day AI review and market memory."""
    return {
        "ai_review": daily_signal_journal.get_daily_ai_review(),
        "market_memory": daily_signal_journal.get_daily_market_memory(),
    }


@router.get("/status")
async def get_live_status() -> Dict[str, Any]:
    """Returns autonomous scheduler, outcome worker, and validation cohort status."""
    meta = canonical_signal_service.get_canonical_runtime_metadata()
    scheduler_status = live_forecast_scheduler.get_status()
    worker_status = shadow_outcome_worker.get_status()

    return {
        "system_status": "LIVE" if not shadow_validation_engine.is_paused else "PAUSED",
        "runtime_phase": meta["runtime_phase"],
        "runtime_status": meta["runtime_status"],
        "git_commit": meta["git_commit"],
        "config_hash": meta["config_hash"],
        "execution_mode": meta["execution_mode"],
        "real_money_status": meta["real_money_status"],
        "scheduler": scheduler_status,
        "outcome_worker": worker_status,
        "validation_cohort": "PHASE_58_5_CANONICAL_COHORT",
        "model_version": "3.2.0-frozen",
        "zero_trust_active": True,
        "timestamps": {
            "last_market_data_at": meta["last_market_data_at"],
            "last_forecast_at": meta["last_forecast_at"],
            "last_consensus_at": meta["last_consensus_at"],
            "last_qualification_at": meta["last_qualification_at"],
            "last_ui_sync_at": meta["last_ui_sync_at"],
        },
        "real_money_execution": "DISABLED_SAFETY_ENFORCED",
    }

