"""
Phase 50 — Actionable Signal & Trade Lifecycle API Routes.

Exposes endpoints for actionable trade timing, pre-entry revalidation, next setup command center,
signal evolution lineages, and authoritative server countdowns.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.core.market_clock import market_clock
from app.decision.actionable_signal_engine import actionable_signal_engine
from app.decision.revalidation_engine import revalidation_engine
from app.runtime.offline_gap_recovery import offline_gap_recovery_engine
from app.logs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/signals", tags=["Phase 50 — Actionable Trade Timing & Lifecycle"])


@router.get("/actionable", summary="Get All Current Actionable Trade Setups")
async def get_actionable_signals(
    include_expired: bool = Query(False, description="Include expired entry windows"),
    asset: Optional[str] = Query(None, description="Filter by asset"),
) -> Dict[str, Any]:
    """
    Returns all qualified actionable trade setups with strict IST timestamps,
    dynamic entry windows, and holding envelopes.
    """
    now = market_clock.get_current_utc()
    opps = actionable_signal_engine.get_actionable_opportunities(include_expired=include_expired)

    if asset:
        opps = [o for o in opps if o.get("asset", "").upper() == asset.upper()]

    # Inject backend authoritative countdown
    for o in opps:
        target_str = o.get("target_time_utc")
        if target_str:
            target_dt = datetime.fromisoformat(target_str)
            o["countdown"] = market_clock.compute_countdown(target_dt, now)

    return {
        "success": True,
        "count": len(opps),
        "server_time_utc": now.isoformat(),
        "server_time_ist": market_clock.format_ist(now),
        "actionable_opportunities": opps,
    }


@router.get("/next-setup", summary="Get Single Most Actionable Upcoming Trade Setup")
async def get_next_actionable_setup() -> Dict[str, Any]:
    """
    Returns the single highest priority trade setup for the Command Center.
    Prioritizes ENTER_NOW -> soonest VALIDATED / WATCH.
    """
    now = market_clock.get_current_utc()
    next_setup = actionable_signal_engine.get_next_actionable_setup()

    if not next_setup:
        return {
            "success": True,
            "has_setup": False,
            "message": "No actionable trade setup currently meets consensus risk thresholds.",
            "server_time_ist": market_clock.format_ist(now),
            "next_setup": None,
        }

    target_str = next_setup.get("target_time_utc")
    countdown = None
    if target_str:
        target_dt = datetime.fromisoformat(target_str)
        countdown = market_clock.compute_countdown(target_dt, now)

    return {
        "success": True,
        "has_setup": True,
        "server_time_utc": now.isoformat(),
        "server_time_ist": market_clock.format_ist(now),
        "countdown": countdown,
        "next_setup": next_setup,
    }


@router.post("/{signal_id}/revalidate", summary="Trigger Immediate Pre-Entry Revalidation")
async def revalidate_signal(signal_id: str) -> Dict[str, Any]:
    """
    Revalidates an existing signal against latest provider market data, evaluates multi-model consensus,
    applies anti-whipsaw hysteresis rules, and generates an immutable versioned record.
    """
    now = market_clock.get_current_utc()
    existing = actionable_signal_engine._actionable_opportunities.get(signal_id)

    if not existing:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found in active opportunities.")

    asset = existing.get("asset", "EURUSD")
    timeframe = existing.get("timeframe", "1H")

    # Fetch fresh provider rates
    try:
        from app.market_data.providers.manager import market_provider_manager
        rates = await market_provider_manager.get_rates(asset, timeframe, count=50)
    except Exception as e:
        logger.error(f"Failed to fetch market data for {asset} during revalidation: {e}")
        rates = None

    if not rates:
        # Fail-closed with DATA_UNAVAILABLE / DATA_STALE
        updated = actionable_signal_engine.revalidate_opportunity(
            signal_id=signal_id,
            current_forecast={
                "asset": asset,
                "direction": existing.get("direction"),
                "confidence": existing.get("confidence"),
                "consensus_score": existing.get("consensus_score"),
                "data_freshness_status": "DATA_STALE",
            },
            now_utc=now,
        )
        return {
            "success": True,
            "revalidation_outcome": "DATA_STALE",
            "message": "Market provider unreachable; signal execution blocked.",
            "updated_signal": updated,
        }

    # Evaluate current market features & consensus
    try:
        import pandas as pd
        latest_close = float(rates[-1].get("close", 0.0)) if rates else float(existing.get("entry_price", 1.0))
        regime = existing.get("market_regime", "TRENDING_BULL")
        quant_sig = existing.get("direction", "NEUTRAL")
        conf_score = float(existing.get("confidence", 0.70))
        agree_score = float(existing.get("consensus_score", 0.75))

        try:
            from app.analytics.feature_engine import FeatureEngine
            from app.strategies.strategy_engine.regime_detector import MarketRegimeDetector
            df = pd.DataFrame(rates)
            df = FeatureEngine.add_all_features(df)
            if "close" in df and len(df) > 0:
                latest_close = float(df["close"].iloc[-1])
            regime_detector = MarketRegimeDetector()
            regime = regime_detector.detect_regime(df)

            from app.analytics.consensus_engine import ConsensusEngine
            consensus_engine = ConsensusEngine()
            c_res = consensus_engine.generate_consensus(asset, timeframe, df)
            quant_sig = c_res.get("signal", quant_sig)
            conf_score = float(c_res.get("confidence_score", 50.0)) / 100.0 if float(c_res.get("confidence_score", 50.0)) > 1.0 else float(c_res.get("confidence_score", 0.5))
            agree_score = float(c_res.get("agreement_percentage", 50.0)) / 100.0 if float(c_res.get("agreement_percentage", 50.0)) > 1.0 else float(c_res.get("agreement_percentage", 0.5))
        except Exception as ml_err:
            logger.warning(f"ML / indicator pipeline fallback during revalidation: {ml_err}")

        curr_forecast = {
            "asset": asset,
            "direction": "BUY" if quant_sig in ["BUY", "BULLISH"] else ("SELL" if quant_sig in ["SELL", "BEARISH"] else "NEUTRAL"),
            "confidence": conf_score,
            "consensus_score": agree_score,
            "market_regime": regime,
            "current_price": latest_close,
            "data_freshness_status": "FRESH",
            "event_risk": existing.get("event_risk", "NONE"),
        }

        updated = actionable_signal_engine.revalidate_opportunity(
            signal_id=signal_id,
            current_forecast=curr_forecast,
            current_market={"price": latest_close},
            now_utc=now,
        )

        return {
            "success": True,
            "revalidation_outcome": updated.get("change_reason", "Revalidation complete"),
            "server_time_ist": market_clock.format_ist(now),
            "updated_signal": updated,
        }

    except Exception as e:
        logger.error(f"Error during revalidation calculation for {signal_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "signal_id": signal_id,
        }


@router.get("/{signal_id}/evolution", summary="Get Signal Evolution History Lineage")
async def get_signal_evolution_history(signal_id: str) -> Dict[str, Any]:
    """
    Returns the immutable timeline of all versions, revalidations, and status changes for a signal.
    """
    parent_id = signal_id.split("-v")[0] if "-v" in signal_id else signal_id
    history = actionable_signal_engine.get_signal_evolution(parent_id)
    if not history:
        history = actionable_signal_engine.get_signal_evolution(signal_id)

    return {
        "success": True,
        "signal_id": signal_id,
        "parent_signal_id": parent_id,
        "total_versions": len(history),
        "evolution_timeline": history,
    }


@router.get("/countdown", summary="Get Authoritative Server Clock & Countdown State")
async def get_clock_countdown(target_utc: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns current server UTC, current IST formatted string, and countdown to target.
    """
    now = market_clock.get_current_utc()
    countdown = None
    if target_utc:
        try:
            # Handle query string '+' decoded as space and Z format
            clean_ts = target_utc.replace(" ", "+").replace("Z", "+00:00")
            t_dt = datetime.fromisoformat(clean_ts)
            countdown = market_clock.compute_countdown(t_dt, now)
        except Exception as e:
            logger.warning(f"Failed to parse target_utc '{target_utc}': {e}")

    return {
        "success": True,
        "server_time_utc": now.isoformat(),
        "server_time_ist": market_clock.format_ist(now),
        "countdown": countdown,
    }

