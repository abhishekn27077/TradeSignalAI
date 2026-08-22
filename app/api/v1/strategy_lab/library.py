from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.database.models.strategy_lab import StrategyLabModel
from app.strategy_lab.lifecycle import strategy_lifecycle

router = APIRouter()

@router.get("/", response_model=list[dict[str, Any]])
async def get_library(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StrategyLabModel))
    strategies = result.scalars().all()
    return [
        {
            "id": strat.id,
            "name": strat.name,
            "version": strat.version,
            "creator": strat.creator,
            "created_at": strat.created_at.isoformat() if strat.created_at else None,
            "performance": strat.performance,
            "supported_assets": strat.supported_assets,
            "timeframes": strat.timeframes,
            "status": strat.status
        }
        for strat in strategies
    ]

@router.post("/{strategy_id}/promote")
async def promote_strategy(strategy_id: str, current_state: str, db: AsyncSession = Depends(get_db)):
    new_state = strategy_lifecycle.promote(strategy_id, current_state)
    result = await db.execute(select(StrategyLabModel).where(StrategyLabModel.id == strategy_id))
    strat = result.scalar_one_or_none()
    if strat:
        strat.status = new_state
        await db.commit()
    return {"strategy_id": strategy_id, "new_state": new_state}
