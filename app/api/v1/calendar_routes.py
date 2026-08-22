"""
Phase 40 — Economic Calendar API Routes.

Endpoints:
  GET /api/v1/calendar/events              — Economic calendar filtered by today/tomorrow/week
  GET /api/v1/calendar/event/{event_id}    — Single event with historical stats and scenarios
  GET /api/v1/calendar/risk/{asset}        — Event risk assessment for a specific asset
"""
from typing import Optional

from fastapi import APIRouter, Query

from app.logs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Economic Calendar"])


@router.get("/calendar/events", summary="Economic Calendar Events")
async def get_calendar_events(
    filter_type: str = Query(default="today", description="Filter: today, tomorrow, week"),
    importance: Optional[str] = Query(default=None, description="Filter: HIGH, MEDIUM, LOW"),
    currency: Optional[str] = Query(default=None, description="Filter: USD, EUR, GBP, JPY, AUD"),
):
    """
    Returns upcoming economic events with:
    - Scheduled time (UTC & IST)
    - 3-way probabilistic scenarios (HOT / IN_LINE / COOL)
    - Asset sensitivity matrices
    - Historical statistics from comparable events
    - Live countdown to event

    Future actual values are ALWAYS unknown until officially released.
    """
    try:
        from app.market_data.economic_calendar import economic_calendar_engine
        events = economic_calendar_engine.get_upcoming_events(
            filter_type=filter_type,
            importance=importance,
            currency=currency,
        )

        # Serialize datetime objects
        serialized = []
        for event in events:
            e = {**event}
            if hasattr(e.get("scheduled_utc"), "isoformat"):
                e["scheduled_utc"] = e["scheduled_utc"].isoformat()
            serialized.append(e)

        return {
            "success": True,
            "filter": filter_type,
            "count": len(serialized),
            "events": serialized,
        }
    except Exception as e:
        logger.error(f"Calendar events error: {e}")
        return {"success": True, "events": [], "count": 0}


@router.get("/calendar/event/{event_id}", summary="Event Analysis")
async def get_event_analysis(event_id: str):
    """
    Returns detailed analysis for a specific event:
    - Pre-event historical statistics
    - 3-way scenario probabilities
    - Asset sensitivity matrix
    - Post-event surprise analysis (if released)
    """
    try:
        from app.market_data.economic_calendar import economic_calendar_engine

        # Search for event in today/week events
        events = economic_calendar_engine.get_upcoming_events("week")
        target = None
        for event in events:
            if event.get("event_id") == event_id:
                target = event
                break

        if not target:
            return {"success": False, "error": "Event not found"}

        # Enrich with historical stats
        template_key = target.get("template_key", "")
        stats = economic_calendar_engine.get_historical_stats(template_key)

        # Serialize datetimes
        if hasattr(target.get("scheduled_utc"), "isoformat"):
            target["scheduled_utc"] = target["scheduled_utc"].isoformat()

        return {
            "success": True,
            "event": target,
            "historical_stats": stats,
        }
    except Exception as e:
        logger.error(f"Event analysis error: {e}")
        return {"success": False, "error": str(e)}


@router.get("/calendar/risk/{asset}", summary="Asset Event Risk")
async def get_asset_event_risk(
    asset: str,
    hours_ahead: int = Query(default=24, le=168, description="Lookahead window in hours"),
):
    """
    Assess event risk level for a specific asset.
    Returns: NONE, LOW, MEDIUM, HIGH, EXTREME

    Used by the forecast engine to gate trade signals during high-risk periods.
    """
    try:
        from app.market_data.economic_calendar import economic_calendar_engine
        risk_level = economic_calendar_engine.get_event_risk_level(asset, hours_ahead)
        return {
            "success": True,
            "asset": asset,
            "hours_ahead": hours_ahead,
            "risk_level": risk_level,
        }
    except Exception as e:
        logger.error(f"Asset event risk error: {e}")
        return {"success": True, "asset": asset, "risk_level": "UNKNOWN"}
