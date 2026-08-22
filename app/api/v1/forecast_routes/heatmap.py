from fastapi import APIRouter

from app.market_intelligence.heatmap_engine import heatmap_engine

router = APIRouter()

@router.get("/current")
async def get_current_heatmap():
    """
    Returns the real-time Market Heatmap metrics.
    """
    heatmap = await heatmap_engine.get_current_heatmap()
    return heatmap
