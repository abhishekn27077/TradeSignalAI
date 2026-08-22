from fastapi import APIRouter, Depends
from app.api.dependencies import require_role

from app.logs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/execution", tags=["execution"])


@router.get("/positions", summary="Get Current Positions")
async def get_positions():
    try:
        from app.execution.router import smart_router
        if hasattr(smart_router, "get_positions"):
            positions = await smart_router.get_positions()
            return {"success": True, "positions": positions}
        return {"success": True, "positions": []}
    except Exception as e:
        logger.warning(f"Positions fetch error: {e}")
        return {"success": True, "positions": []}


@router.get("/orders", summary="Get Open Orders")
async def get_orders():
    try:
        from app.execution.router import smart_router
        if hasattr(smart_router, "get_orders"):
            orders = await smart_router.get_orders()
            return {"success": True, "orders": orders}
        return {"success": True, "orders": []}
    except Exception as e:
        logger.warning(f"Orders fetch error: {e}")
        return {"success": True, "orders": []}


@router.get("/balance", summary="Get Account Balance")
async def get_balance():
    try:
        from app.execution.router import smart_router
        if hasattr(smart_router, "get_balance"):
            balance = await smart_router.get_balance()
            return {"success": True, **balance}
        return {"success": True, "balance": 0, "equity": 0, "margin": 0, "free_margin": 0}
    except Exception as e:
        logger.warning(f"Balance fetch error: {e}")
        return {"success": True, "balance": 0, "equity": 0, "margin": 0, "free_margin": 0}


@router.post("/cancel/{order_id}", summary="Cancel Order", dependencies=[Depends(require_role(["admin", "trader"]))])
async def cancel_order(order_id: str):
    try:
        from app.execution.router import smart_router
        if hasattr(smart_router, "cancel_order"):
            result = await smart_router.cancel_order(order_id)
            return {"success": True, "message": "Order cancelled", "order_id": order_id, "result": result}
        return {"success": True, "message": "Cancel not available on broker router"}
    except Exception as e:
        logger.warning(f"Cancel order error: {e}")
        return {"success": False, "message": "Failed to cancel order", "order_id": order_id}