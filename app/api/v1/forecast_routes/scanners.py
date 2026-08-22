from fastapi import APIRouter

router = APIRouter(prefix="/scanners", tags=["Forecast Scanners"])

@router.post("/swing/run", summary="Trigger Swing Scanner")
async def run_swing_scanner():
    # A manual trigger endpoint if needed
    return {"status": "success", "message": "Scanner triggered"}

@router.post("/h4/run", summary="Trigger H4 Engine")
async def run_h4_engine():
    import asyncio

    from app.market_intelligence.h4_engine import h4_forecast_engine
    asyncio.create_task(h4_forecast_engine.generate_forecasts())
    return {"status": "success", "message": "H4 Engine triggered"}
