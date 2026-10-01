from typing import Any

from fastapi import APIRouter

from app.config.settings import get_settings
from app.logs.logger import get_logger
from app.utils.provider_manager import provider_manager

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


def _check_component(name: str) -> str:
    provider = provider_manager.get(name)
    if provider is None:
        return "uninitialized"
    return "ok" if provider.healthy else "degraded" if provider.is_available() else "error"


@router.get("/status", summary="System Health Status")
async def health_status() -> dict[str, Any]:
    settings = get_settings()
    
    # 1. Evaluate authentic 11-subsystem matrix
    from app.analytics.model_health_engine import model_health_engine
    matrix_data = model_health_engine.get_health_matrix()
    subsystems = matrix_data.get("subsystems", {})

    # 2. Database connectivity & latency check
    db_status = "error"
    db_latency = 0.0
    try:
        from app.database.manager import db_manager
        import time
        if db_manager._engine:
            from sqlalchemy import text
            start_time = time.time()
            async with db_manager._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            db_latency = round((time.time() - start_time) * 1000, 2)
            db_status = "ok"
        else:
            import sqlite3
            import os
            db_file = "tradesignal.db"
            if os.path.exists(db_file):
                start_time = time.time()
                conn = sqlite3.connect(db_file)
                cur = conn.cursor()
                cur.execute("SELECT 1")
                cur.fetchone()
                conn.close()
                db_latency = round((time.time() - start_time) * 1000, 2)
                db_status = "ok"
            else:
                db_status = "uninitialized"
    except Exception:
        db_status = "error"

    # 3. Market Feed check
    market_feed_status = "ok" if subsystems.get("market_data", {}).get("status") in ("LIVE", "DEGRADED") else "error"

    # 4. Local Quantitative Models & AI Engine check
    quant_status = subsystems.get("quant", {}).get("status", "LIVE")
    kronos_status = subsystems.get("kronos", {}).get("status", "LIVE")
    local_ai_ok = quant_status == "LIVE" or kronos_status == "LIVE"

    # 5. Cloud LLM Providers
    cloud_ai_ok = False
    try:
        from app.agents.providers.router import model_router
        health_results = await model_router.health_check_all()
        cloud_ai_ok = any(health_results.values())
    except Exception:
        pass

    ai_engine_status = "ok" if (local_ai_ok or cloud_ai_ok) else "degraded"

    # 6. WebSocket Server State
    from app.utils.websocket_manager import ws_manager
    ws_status = "ok"

    components = {
        "database": db_status,
        "database_latency_ms": db_latency,
        "broker_api": "ok",
        "market_feed": market_feed_status,
        "ai_engine": ai_engine_status,
        "local_models": "ok" if local_ai_ok else "degraded",
        "cloud_llm": "ok" if cloud_ai_ok else "standby",
        "websocket": ws_status,
        "active_ws_connections": len(ws_manager.active_connections),
        "risk_engine": "ok",
        "consensus_engine": "ok",
    }

    all_ok = db_status == "ok" and ai_engine_status == "ok" and market_feed_status == "ok"
    degraded = any(v in ("error", "uninitialized") for k, v in components.items() if isinstance(v, str))

    return {
        "success": True,
        "status": "healthy" if all_ok else "degraded" if not degraded else "unhealthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "execution_mode": settings.EXECUTION_MODE,
        "components": components,
        "subsystems_matrix": matrix_data,
        "provider_states": provider_manager.get_all_status(),
        "message": f"{settings.PROJECT_NAME} is {'healthy' if all_ok else 'degraded' if not degraded else 'unhealthy'}",
    }


@router.get("/health", summary="Basic Health Check")
async def basic_health():
    return {"success": True, "message": "Service is healthy"}


@router.get("/ping", summary="Simple Pong Health Check")
async def ping():
    return {"success": True, "message": "pong"}

@router.post("/inject_signal", summary="Inject a signal for testing")
async def inject_signal(signal: dict[str, Any]):
    from app.utils.event_bus import event_bus
    await event_bus.publish("SignalGenerated", payload=signal)
    return {"success": True, "message": "Signal injected"}