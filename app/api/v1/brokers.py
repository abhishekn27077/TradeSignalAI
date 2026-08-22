
from fastapi import APIRouter

from app.logs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/brokers", tags=["brokers"])


@router.get("/status", summary="Get Broker Status")
async def broker_status():
    try:
        from app.execution.router import smart_router
        routers = smart_router.list_brokers() if hasattr(smart_router, "list_brokers") else {}
        return {"success": True, "brokers": routers, "count": len(routers) if isinstance(routers, dict) else 0}
    except Exception as e:
        logger.warning(f"Broker status error: {e}")
        return {"success": True, "brokers": {}, "count": 0, "note": "No brokers configured"}


@router.post("/sync", summary="Sync Broker State")
async def broker_sync():
    try:
        from app.execution.router import smart_router
        if hasattr(smart_router, "sync_all"):
            await smart_router.sync_all()
            return {"success": True, "message": "Broker sync requested"}
        return {"success": True, "message": "No sync method available on broker router"}
    except Exception as e:
        logger.warning(f"Broker sync error: {e}")
        return {"success": True, "message": "Broker sync unavailable", "note": str(e)}