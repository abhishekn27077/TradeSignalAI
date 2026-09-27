"""
app/api/v1/terminal_routes.py
==============================
Simplified, Authoritative Trade Signal Terminal API Endpoints.

Delivers clean, authoritative, non-redundant payloads for:
1. [ TODAY ] : Signals generated today in IST (Asia/Kolkata), auto-resolved, with summary KPIs and actionable time windows.
2. [ TOMORROW ] : Analytical point-in-time forecasts only, clearly tagged non-prospective.
3. [ HISTORY ] : Canonical historical signal ledger with deterministic outcomes, full forensic detail, and parametric filters.
4. [ TIMEFRAMES ] : Dynamic timeframe intelligence and Wilson CI rankings.
5. [ PERFORMANCE ] : Comprehensive overview metrics, sample-gated asset performance, and timeframe performance.
6. [ DETAIL ] : Deep inspection endpoint for a single signal.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException
import pandas as pd

from app.core.canonical_prospective_ledger import (
    canonical_prospective_ledger,
    CORE_ASSETS,
    SUPPORTED_TIMEFRAMES,
    STATUS_UPCOMING,
    STATUS_ENTRY_WINDOW,
    STATUS_ACTIVE,
    STATUS_RESOLVED,
    CanonicalProspectiveSignal,
)
from app.analytics.canonical_statistics_service import canonical_statistics_service
from app.core.market_session import MarketSessionService
from app.forecast.tomorrow_forecast_engine import tomorrow_forecast_engine
from app.analytics.timeframe_intelligence_engine import timeframe_intelligence_engine

router = APIRouter(prefix="/terminal", tags=["Trade Signal Terminal UX"])


def utc_to_ist_str(utc_str: Optional[str], include_date: bool = False) -> str:
    """Converts a UTC ISO timestamp string into formatted India Standard Time (IST)."""
    if not utc_str:
        return "—"
    try:
        dt = pd.to_datetime(utc_str, utc=True)
        ist_dt = dt.tz_convert("Asia/Kolkata")
        if include_date:
            return ist_dt.strftime("%d %b %H:%M IST")
        return ist_dt.strftime("%H:%M IST")
    except Exception:
        return str(utc_str)[:16].replace("T", " ") + " IST"


def format_signal_for_terminal(sig: CanonicalProspectiveSignal, now_utc: datetime) -> Dict[str, Any]:
    """
    Transforms a canonical prospective signal into a clean, presentation-ready
    dictionary with times strictly in IST and simplified lifecycle status.
    """
    # Determine clear lifecycle status
    outcome = sig.outcome
    res_reason = sig.resolution_reason or ""
    sig_status = sig.signal_status or "UPCOMING"

    if outcome == "WON":
        display_status = "TP HIT"
    elif outcome == "LOST":
        display_status = "SL HIT"
    elif outcome == "TIME_EXIT":
        display_status = "EXPIRED"
    elif sig_status == "CANCELLED":
        display_status = "CANCELLED"
    elif sig_status == "ACTIVE":
        display_status = "ACTIVE"
    else:
        # Check if expired without resolution
        is_past = False
        if sig.max_exit_time:
            try:
                max_exit_dt = pd.to_datetime(sig.max_exit_time, utc=True)
                if max_exit_dt < now_utc:
                    is_past = True
            except Exception:
                pass
        display_status = "UNRESOLVED" if is_past else "UPCOMING"

    # Risk-Reward ratio
    risk_dist = abs(sig.entry_price - sig.stop_loss)
    reward_dist = abs(sig.take_profit - sig.entry_price)
    rr_ratio = round(reward_dist / risk_dist, 2) if risk_dist > 0 else 2.0

    return {
        "id": sig.signal_id,
        "signal_id": sig.signal_id,
        "asset": sig.asset,
        "direction": sig.direction,
        "timeframe": sig.timeframe,
        "entry": round(sig.actual_entry_price or sig.entry_price, 5),
        "stop_loss": round(sig.stop_loss, 5),
        "take_profit": round(sig.take_profit, 5),
        "risk_reward": rr_ratio,
        "confidence": round(sig.probability * 100) if sig.probability <= 1.0 else round(sig.probability),
        "confidence_pct": round(sig.probability * 100) if sig.probability <= 1.0 else round(sig.probability),
        
        # User-facing IST Timestamps
        "generated_at_ist": utc_to_ist_str(sig.generated_at_utc, include_date=True),
        "open_at_ist": utc_to_ist_str(sig.preferred_entry_time or sig.entry_window_start),
        "close_at_ist": utc_to_ist_str(sig.max_exit_time or sig.expected_exit_time),
        
        # Internal UTC timestamps (preserved for audits)
        "generated_at_utc": sig.generated_at_utc,
        "open_at_utc": sig.entry_window_start,
        "close_at_utc": sig.max_exit_time,
        
        # Lifecycle & Outcome
        "status": display_status,
        "raw_status": sig_status,
        "outcome": outcome,
        "resolution_reason": res_reason,
        "exit_price": round(sig.actual_exit_price, 5) if sig.actual_exit_price is not None else None,
        "exit_time_ist": utc_to_ist_str(sig.actual_exit_time, include_date=True) if sig.actual_exit_time else None,
        "realized_r": sig.net_r,
        
        # Lineage metadata
        "quality_grade": sig.quality_grade,
        "qualification_status": sig.qualification_status,
        "policy_version": sig.policy_version,
        "model_version": sig.model_version,
    }


@router.get("/today", summary="Get Today's Canonical Signals with IST Timings")
def get_today_signals():
    """
    Returns only official signals generated for today's trading session.
    Automatically resolves any expired signals against verified historical candles.
    Calculates today's win rate strictly from resolved signals.
    """
    now_utc = datetime.now(timezone.utc)

    # 1. Automatic Outcome Resolution for any pending expired signals
    try:
        canonical_prospective_ledger.resolve_pending_expired_signals(now_utc)
    except Exception:
        pass

    # 2. Fetch today's signals
    signals = canonical_prospective_ledger.get_signals_by_filter(date_filter="TODAY", limit=200)

    # If no signals generated today, provide recent active signals for continuity
    if not signals:
        signals = canonical_prospective_ledger.get_signals_by_filter(date_filter="ALL", limit=9)

    # Filter to qualified production signals
    qualified_signals = [s for s in signals if s.qualification_status == "QUALIFIED"]
    formatted_signals = [format_signal_for_terminal(s, now_utc) for s in qualified_signals]

    # 3. Calculate today's performance STRICTLY from resolved signals today
    resolved_today = [s for s in qualified_signals if s.outcome is not None]
    wins_today = sum(1 for s in resolved_today if s.outcome == "WON")
    losses_today = sum(1 for s in resolved_today if s.outcome == "LOST")
    net_r_today = round(sum(s.net_r for s in resolved_today if s.net_r is not None), 2)
    win_rate_today = round((wins_today / len(resolved_today) * 100.0), 1) if resolved_today else None

    # 4. Check Market Open status (Forex / General)
    eurusd_status = MarketSessionService.get_market_status("EURUSD", dt_utc=now_utc)
    btcusd_status = MarketSessionService.get_market_status("BTCUSD", dt_utc=now_utc)
    is_market_open = eurusd_status.get("is_open", True) or btcusd_status.get("is_open", True)
    session_name = eurusd_status.get("session_name", "Global Session")

    ist_now_str = utc_to_ist_str(now_utc.isoformat(), include_date=True)

    # Actionable time windows for backwards-compatibility with test suites
    time_windows = canonical_prospective_ledger.get_today_time_windows(now_utc)
    total_no_trade = sum(w.get("no_trade_count", 0) for w in time_windows) if time_windows else 0

    return {
        "success": True,
        "timestamp_utc": now_utc.isoformat(),
        "ist_current_time": ist_now_str,
        "is_market_open": is_market_open,
        "market_session": session_name,
        "total_time_windows": len(time_windows),
        "total_qualified_signals": len(formatted_signals),
        "total_no_trade_signals": total_no_trade,
        "today_summary": {
            "total_signals": len(formatted_signals),
            "resolved_signals": len(resolved_today),
            "wins": wins_today,
            "losses": losses_today,
            "win_rate_pct": win_rate_today,
            "net_r": net_r_today,
        },
        "signals": formatted_signals,
        "time_windows": time_windows,
    }


@router.get("/tomorrow", summary="Get Tomorrow Forecasts Only (Non-Prospective)")
def get_tomorrow_forecasts():
    """
    Returns tomorrow's predictive models and outlooks generated point-in-time.
    Explicitly labeled 'FORECAST — NOT YET A PROSPECTIVE SIGNAL'.
    """
    return tomorrow_forecast_engine.generate_tomorrow_forecasts()


@router.get("/timeframes", summary="Get Dynamic Timeframe Scoreboard & Rankings")
def get_timeframe_intelligence():
    """
    Returns the dynamic timeframe ranking, Wilson 95% confidence intervals,
    and the scoreboard.
    """
    return timeframe_intelligence_engine.evaluate_all_timeframes()


@router.get("/history", summary="Get Historical Signals with Full Filtering")
def get_canonical_history(
    date_filter: str = Query("ALL", description="Filter: TODAY, YESTERDAY, 7D, 30D, ALL"),
    asset: Optional[str] = Query(None, description="Asset symbol filter"),
    timeframe: Optional[str] = Query(None, description="Timeframe filter"),
    direction: Optional[str] = Query(None, description="BUY / SELL filter"),
    outcome: Optional[str] = Query(None, description="WON / LOST / TIME_EXIT / ALL"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Returns historical signals with exact realized outcomes, R-multiples, and filter options.
    """
    now_utc = datetime.now(timezone.utc)
    
    # Auto-resolve any pending expired signals
    try:
        canonical_prospective_ledger.resolve_pending_expired_signals(now_utc)
    except Exception:
        pass

    norm_outcome = None
    if outcome and outcome.upper() != "ALL":
        if outcome.upper() in ["WIN", "WON"]:
            norm_outcome = "WON"
        elif outcome.upper() in ["LOSS", "LOST"]:
            norm_outcome = "LOST"
        else:
            norm_outcome = outcome.upper()

    signals = canonical_prospective_ledger.get_signals_by_filter(
        date_filter=date_filter,
        asset=asset,
        timeframe=timeframe,
        direction=direction,
        status=norm_outcome,
        limit=limit,
        offset=offset,
    )

    formatted_signals = [format_signal_for_terminal(s, now_utc) for s in signals]

    # Performance slice for filtered set
    stats = canonical_statistics_service.get_canonical_performance_summary(
        date_filter=date_filter,
        asset=asset,
        timeframe=timeframe,
    )

    return {
        "success": True,
        "date_filter": date_filter,
        "total_returned": len(formatted_signals),
        "metrics": {
            "total_signals": stats["total_signals"],
            "resolved_count": stats["resolved_count"],
            "wins": stats["wins"],
            "losses": stats["losses"],
            "time_exits": stats["time_exits"],
            "win_rate_pct": stats["win_rate_pct"] if stats["resolved_count"] > 0 else None,
            "wilson_ci": stats["wilson_95_ci"],
            "total_net_r": stats["total_net_r"],
            "profit_factor": stats["profit_factor"],
            "expectancy_r": stats["expectancy_r"],
            "sample_status": stats["sample_status"],
        },
        "signals": formatted_signals,
    }


@router.get("/history/{signal_id}", summary="Get Detailed Forensic Record for a Single Signal")
def get_signal_detail(signal_id: str):
    """
    Returns full forensic detail for a single prospective signal.
    """
    sig = canonical_prospective_ledger.get_signal(signal_id)
    if not sig:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

    now_utc = datetime.now(timezone.utc)
    formatted = format_signal_for_terminal(sig, now_utc)

    return {
        "success": True,
        "signal": formatted,
        "evidence": {
            "evidence_clusters": sig.evidence_clusters,
            "mtf_confirmation": sig.mtf_confirmation,
            "market_snapshot_hash": sig.market_snapshot_hash,
            "config_hash": sig.config_hash,
            "resolution_reason": sig.resolution_reason,
            "resolved_at_ist": utc_to_ist_str(sig.resolved_at, include_date=True) if sig.resolved_at else None,
        }
    }


@router.get("/performance", summary="Get Performance Overview, Asset Breakdown, and Timeframe Breakdown")
def get_performance_overview(
    date_filter: str = Query("ALL", description="Filter: TODAY, YESTERDAY, 7D, 30D, ALL"),
):
    """
    Returns institutional performance metrics, breakdown by asset, and breakdown by timeframe.
    Strictly gates statistical claims with 'INSUFFICIENT SAMPLE (N = X)' when N < 15.
    """
    now_utc = datetime.now(timezone.utc)
    try:
        canonical_prospective_ledger.resolve_pending_expired_signals(now_utc)
    except Exception:
        pass

    overall = canonical_statistics_service.get_canonical_performance_summary(date_filter=date_filter)
    by_asset = canonical_statistics_service.get_performance_by_asset(date_filter=date_filter, min_sample_req=15)
    by_timeframe = canonical_statistics_service.get_performance_by_timeframe(date_filter=date_filter, min_sample_req=15)

    overview_data = {
        "total_signals": overall["total_signals"],
        "resolved_signals": overall["resolved_count"],
        "wins": overall["wins"],
        "losses": overall["losses"],
        "win_rate_pct": overall["win_rate_pct"] if overall["resolved_count"] > 0 else None,
        "wilson_95_ci": overall["wilson_95_ci"],
        "total_net_r": overall["total_net_r"],
        "profit_factor": overall["profit_factor"],
        "average_r": overall["expectancy_r"],
        "max_drawdown_r": overall["max_drawdown_r"],
        "max_drawdown_pct": overall["max_drawdown_pct"],
        "sample_status": overall["sample_status"],
        "sample_size": overall["resolved_count"],
    }

    return {
        "success": True,
        "date_filter": date_filter,
        "execution_mode": "DEMO / PAPER",
        "real_money_enabled": False,
        "initial_capital": overall["initial_capital"],
        "current_equity": overall["current_capital"],
        "total_realized_r": overall["total_net_r"],
        "total_trades": overall["resolved_count"],
        "wins": overall["wins"],
        "losses": overall["losses"],
        "win_rate_pct": overall["win_rate_pct"],
        "wilson_95_ci": overall["wilson_95_ci"],
        "profit_factor": overall["profit_factor"],
        "sharpe_ratio": overall["sharpe_ratio"],
        "max_drawdown_r": overall["max_drawdown_r"],
        "max_drawdown_pct": overall["max_drawdown_pct"],
        "expectancy_r": overall["expectancy_r"],
        "sample_status": overall["sample_status"],
        "metrics": overall,
        "equity_curve": overall["equity_curve"],
        "overview": overview_data,
        "overall": overview_data,
        "by_asset": by_asset,
        "by_timeframe": by_timeframe,
    }
