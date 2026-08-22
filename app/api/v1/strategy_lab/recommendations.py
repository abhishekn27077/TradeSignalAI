
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.database.models.strategy_lab import StrategyLabModel

router = APIRouter()

@router.get("/")
async def get_recommendations(db: AsyncSession = Depends(get_db)):
    """
    Returns AI suggestions based on historical evidence.
    Generates recommendations on the fly based on active strategies.
    """
    result = await db.execute(select(StrategyLabModel))
    strategies = result.scalars().all()
    recommendations = []
    
    for strat in strategies:
        win_rate = strat.performance.get("win_rate", 0)
        if strat.status == "Qualified" and win_rate < 50.0:
            recommendations.append({
                "action": "Retire", 
                "target": strat.id, 
                "reason": f"Win rate ({win_rate}%) is below 50% threshold for Qualified status."
            })
            
    if not recommendations:
        # Fallback empty state
        return []
        
    return recommendations
