"""
app/api/v1/terminal_routes.py
==============================
Simplified Trade Signal Terminal API Endpoints (Phase 70).

Delivers clean, authoritative, non-redundant payloads for:
- [ TODAY ] : Signals generated today grouped by actionable time window with exact entry windows & hold times.
- [ TOMORROW ] : Analytical point-in-time forecasts only, clearly tagged non-prospective.
- [ HISTORY ] : Canonical historical signal ledger with deterministic outcomes (Today, Yesterday, 7D, 30D, All).
- [ PERFORMANCE ] : Timeframe scoreboard, Best/Second Best ranking, Wilson CI, Paper Portfolio equity & risk.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from app.core.canonical_prospective_ledger import (
    canonical_prospective_ledger,
    CORE_ASSETS,
    SUPPORTED_TIMEFRAMES,
    STATUS_UPCOMING,
    STATUS_ENTRY_WINDOW,
    STATUS_ACTIVE,
    STATUS_RESOLVED,
)
from app.analytics.timeframe_intelligence_engine import timeframe_intelligence_engine
from app.analytics.paper_portfolio_engine import paper_portfolio_engine
from app.analytics.canonical_statistics_service import canonical_statistics_service
from app.forecast.tomorrow_forecast_engine import tomorrow_forecast_engine

router = APIRouter(prefix="/terminal", tags=["Trade Signal Terminal UX"])


@router.get("/today", summary="Get Today's Signals Grouped by Time Window")
def get_today_terminal_signals():
    """
    Returns only signals generated today, grouped by actionable signal time window
    (e.g., '18:00 SIGNAL WINDOW'), with exact timing windows, price levels, and
    isolated no-trade reasons.
    """
    time_windows = canonical_prospective_ledger.get_today_time_windows()
    tf_summary = timeframe_intelligence_engine.evaluate_all_timeframes()

    total_qualified = sum(w["qualified_count"] for w in time_windows)
    total_no_trade = sum(w["no_trade_count"] for w in time_windows)

    return {
        "success": True,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_time_windows": len(time_windows),
        "total_qualified_signals": total_qualified,
        "total_no_trade_signals": total_no_trade,
        "best_observed_timeframe": tf_summary.get("best_observed_timeframe", "4H"),
        "second_best_timeframe": tf_summary.get("second_best_timeframe", "1H"),
        "time_windows": time_windows,
    }


@router.get("/tomorrow", summary="Get Tomorrow Forecasts Only (Non-Prospective)")
def get_tomorrow_forecasts():
    """
    Returns tomorrow's predictive models and outlooks generated point-in-time.
    Explicitly labeled 'FORECAST — NOT YET A PROSPECTIVE SIGNAL'.
    """
    return tomorrow_forecast_engine.generate_tomorrow_forecasts()


@router.get("/history", summary="Get Canonical Signal History with Realized Outcomes")
def get_canonical_history(
    date_filter: str = Query("ALL", description="Filter by horizon: TODAY, YESTERDAY, 7D, 30D, ALL"),
    asset: Optional[str] = Query(None, description="Asset symbol filter"),
    timeframe: Optional[str] = Query(None, description="Timeframe filter"),
    direction: Optional[str] = Query(None, description="BUY / SELL filter"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Returns the authoritative historical signal stream directly from SQLite.
    Guarantees no duplicates and exact mathematical consistency.
    """
    signals = canonical_prospective_ledger.get_signals_by_filter(
        date_filter=date_filter,
        asset=asset,
        timeframe=timeframe,
        direction=direction,
        limit=limit,
        offset=offset,
    )

    # Compute aggregate summary using Canonical Statistics Service
    stats = canonical_statistics_service.get_canonical_performance_summary(
        date_filter=date_filter,
        asset=asset,
        timeframe=timeframe,
    )

    return {
        "success": True,
        "date_filter": date_filter,
        "total_returned": len(signals),
        "metrics": {
            "resolved_count": stats["resolved_count"],
            "wins": stats["wins"],
            "losses": stats["losses"],
            "time_exits": stats["time_exits"],
            "win_rate_pct": stats["win_rate_pct"],
            "wilson_ci": stats["wilson_95_ci"],
            "total_net_r": stats["total_net_r"],
            "profit_factor": stats["profit_factor"],
            "expectancy_r": stats["expectancy_r"],
            "sample_status": stats["sample_status"],
        },
        "signals": [s.to_dict() for s in signals],
    }


@router.get("/timeframes", summary="Get Dynamic Timeframe Scoreboard & Rankings")
def get_timeframe_intelligence():
    """
    Returns the dynamic timeframe ranking, Wilson 95% confidence intervals,
    and the simplified scoreboard.
    """
    return timeframe_intelligence_engine.evaluate_all_timeframes()


@router.get("/performance", summary="Get Paper Portfolio Equity Curve & Risk Metrics")
def get_paper_performance(
    date_filter: str = Query("ALL", description="Filter by horizon: TODAY, YESTERDAY, 7D, 30D, ALL"),
):
    """
    Returns the virtual $100k paper portfolio metrics, fixed-R accounting,
    and cumulative equity curve computed authoritatively from SQLite.
    """
    stats = canonical_statistics_service.get_canonical_performance_summary(date_filter=date_filter)

    return {
        "success": True,
        "execution_mode": "DEMO / PAPER",
        "real_money_enabled": False,
        "initial_capital": stats["initial_capital"],
        "current_equity": stats["current_capital"],
        "total_realized_r": stats["total_net_r"],
        "total_trades": stats["resolved_count"],
        "wins": stats["wins"],
        "losses": stats["losses"],
        "win_rate_pct": stats["win_rate_pct"],
        "wilson_95_ci": stats["wilson_95_ci"],
        "profit_factor": stats["profit_factor"],
        "sharpe_ratio": stats["sharpe_ratio"],
        "max_drawdown_r": stats["max_drawdown_r"],
        "max_drawdown_pct": stats["max_drawdown_pct"],
        "expectancy_r": stats["expectancy_r"],
        "sample_status": stats["sample_status"],
        "metrics": stats,
        "equity_curve": stats["equity_curve"],
    }
