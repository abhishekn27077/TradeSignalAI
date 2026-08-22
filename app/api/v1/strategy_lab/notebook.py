
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.database.models.strategy_lab import StrategyNotebookModel

router = APIRouter()

@router.get("/")
async def get_notebooks(db: AsyncSession = Depends(get_db)) -> list[dict[str, str]]:
    """
    Returns structured research logs.
    """
    result = await db.execute(select(StrategyNotebookModel))
    notebooks = result.scalars().all()
    return [
        {
            "id": nb.id,
            "title": nb.title,
            "content": nb.content,
            "tags": nb.tags,
            "created_at": nb.created_at.isoformat() if nb.created_at else None
        }
        for nb in notebooks
    ]
