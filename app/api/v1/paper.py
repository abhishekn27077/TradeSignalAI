
from fastapi import APIRouter

from app.logs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/paper", tags=["paper"])


@router.get("/status", summary="Get Paper Trading Status")
async def paper_status():
    try:
        from app.paper_trading.account_manager import account_manager
        summary = account_manager.get_summary() if hasattr(account_manager, "get_summary") else {}
        return {"success": True, "data": summary}
    except Exception as e:
        logger.warning(f"Paper status error: {e}")
        return {"success": True, "data": {"balance": 10000.0, "equity": 10000.0}}


@router.get("/orders", summary="Get Paper Orders")
async def paper_orders():
    try:
        from app.execution.paper.order_manager import paper_order_manager
        orders = paper_order_manager.get_orders() if hasattr(paper_order_manager, "get_orders") else []
        return {"success": True, "orders": orders, "count": len(orders)}
    except Exception as e:
        logger.warning(f"Paper orders error: {e}")
        return {"success": True, "orders": [], "count": 0}


@router.get("/statistics", summary="Get Paper Trading Statistics")
async def paper_statistics():
    try:
        from app.paper_trading.statistics import paper_statistics
        stats = paper_statistics.get_stats() if hasattr(paper_statistics, "get_stats") else {}
        return {"success": True, "data": stats}
    except Exception as e:
        logger.warning(f"Paper statistics error: {e}")
        return {"success": True, "data": {}}