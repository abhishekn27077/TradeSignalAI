
from fastapi import APIRouter, Query

from app.logs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/journal", tags=["journal"])


@router.get("/trades", summary="Get Trade History")
async def get_trades(limit: int = Query(default=100, le=1000), offset: int = Query(default=0, ge=0)):
    try:
        from app.journal.manager import journal_manager
        trades = await journal_manager.get_trades(limit=limit, offset=offset)
        return {"success": True, "trades": trades, "count": len(trades)}
    except Exception as e:
        logger.warning(f"Journal trades error: {e}")
        return {"success": True, "trades": [], "count": 0}


@router.get("/trades/{trade_id}", summary="Get Trade by ID")
async def get_trade(trade_id: str):
    try:
        from app.journal.manager import journal_manager
        trade = await journal_manager.get_trade(trade_id)
        if trade is None:
            return {"success": False, "message": f"Trade {trade_id} not found"}
        return {"success": True, "trade": trade}
    except Exception as e:
        logger.warning(f"Journal trade error: {e}")
        return {"success": False, "message": str(e)}


@router.get("/statistics", summary="Get Trade Statistics")
async def get_statistics():
    try:
        from app.journal.manager import journal_manager
        stats = await journal_manager.get_statistics()
        return {"success": True, **stats}
    except Exception as e:
        logger.warning(f"Journal statistics error: {e}")
        return {"success": True, "total_trades": 0, "winning_trades": 0, "losing_trades": 0, "win_rate": 0, "total_pnl": 0, "avg_pnl": 0}


@router.post("/trades/{trade_id}/review", summary="AI-Review a Trade")
async def review_trade(trade_id: str):
    try:
        from app.journal.ai_reviewer import ai_reviewer
        from app.journal.manager import journal_manager
        trade = await journal_manager.get_trade(trade_id)
        if trade is None:
            return {"success": False, "message": f"Trade {trade_id} not found"}
        review = await ai_reviewer.review_trade(trade)
        return {"success": True, "review": review}
    except Exception as e:
        logger.warning(f"Trade review error: {e}")
        return {"success": False, "message": str(e)}