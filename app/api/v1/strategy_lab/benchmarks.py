
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.database.models.strategy_lab import StrategyBenchmarkModel

router = APIRouter()

@router.get("/")
async def get_benchmarks(db: AsyncSession = Depends(get_db)):
    """
    Returns leaderboard data.
    """
    result = await db.execute(select(StrategyBenchmarkModel))
    benchmarks = result.scalars().all()
    return {
        "leaderboard": [
            {
                "strategy": bm.name,
                "metrics": bm.metrics
            }
            for bm in benchmarks
        ]
    }
