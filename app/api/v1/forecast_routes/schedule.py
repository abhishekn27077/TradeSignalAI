from fastapi import APIRouter

from app.market_intelligence.schedule_engine import schedule_engine

router = APIRouter()

@router.get("/status")
async def get_schedule_status():
    """
    Returns the live countdown and next forecast generation time.
    """
    return schedule_engine.get_schedule_status()

@router.get("/h4")
async def get_h4_planner():
    """
    Returns the H4 session planner timeline for the next 24 hours.
    """
    now_ist = schedule_engine._get_ist_time()
    next_h4 = schedule_engine._get_next_h4_time(now_ist)
    
    from datetime import timedelta
    sessions = []
    current_target = next_h4
    for _ in range(6): # Next 6 H4 candles = 24h
        sessions.append({
            "forecast_time_ist": current_target.isoformat(),
            "status": "Scheduled"
        })
        current_target += timedelta(hours=4)
        
    return {"planner": sessions}
