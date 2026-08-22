
from fastapi import APIRouter, HTTPException

from app.market_intelligence.outlook import outlook_generator

router = APIRouter(prefix="/outlook", tags=["Forecast Outlook"])

@router.get("/daily", summary="Get Daily Outlook")
async def get_daily_outlook():
    try:
        outlook = await outlook_generator.generate_daily_outlook()
        return {"status": "success", "data": outlook}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weekly", summary="Get Weekly Outlook")
async def get_weekly_outlook():
    try:
        outlook = await outlook_generator.generate_weekly_outlook()
        return {"status": "success", "data": outlook}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
