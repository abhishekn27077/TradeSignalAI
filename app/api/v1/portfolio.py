
from fastapi import APIRouter

from app.logs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/summary", summary="Get Portfolio Summary")
async def portfolio_summary():
    try:
        from app.paper_trading.account_manager import account_manager
        summary = account_manager.get_summary() if hasattr(account_manager, "get_summary") else {}
        return {"success": True, "data": summary}
    except Exception as e:
        logger.warning(f"Portfolio summary error: {e}")
        return {"success": True, "data": {"balance": 0, "equity": 0}}


@router.get("/allocation", summary="Get Target Allocation")
async def target_allocation():
    try:
        from app.portfolio.optimizer import portfolio_optimizer
        allocation = await portfolio_optimizer.get_target_allocation() if hasattr(portfolio_optimizer, "get_target_allocation") else {}
        return {"success": True, "data": allocation}
    except Exception as e:
        logger.warning(f"Allocation error: {e}")
        return {"success": True, "data": {}}