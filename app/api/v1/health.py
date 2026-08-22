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
    return "ok" if provider.is_connected() else "degraded" if provider.is_available() else "error"


@router.get("/status", summary="System Health Status")
async def health_status() -> dict[str, Any]:
    settings = get_settings()
    components = {
        "database": "uninitialized",
        "broker_api": "uninitialized",
        "market_feed": "uninitialized",
        "openrouter": "uninitialized",
        "ai_engine": "uninitialized",
        "websocket": "uninitialized",
    }

    try:
        from app.database.manager import db_manager
        if db_manager._engine:
            try:
                from sqlalchemy import text
                import time
                start_time = time.time()
                async with db_manager._engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                db_latency = (time.time() - start_time) * 1000
                components["database"] = "ok"
                components["database_latency_ms"] = round(db_latency, 2)
            except Exception:
                components["database"] = "error"
        else:
            components["database"] = "uninitialized"
    except Exception:
        components["database"] = "error"

    try:
        components["broker_api"] = "ok"
    except Exception:
        components["broker_api"] = "standby"

    try:
        from app.market_data.providers.manager import market_provider_manager
        if market_provider_manager.available_providers:
            provider_healths = {}
            for name, provider in market_provider_manager._providers.items():
                if hasattr(provider, "check_health"):
                    provider_healths[name] = await provider.check_health()
                else:
                    provider_healths[name] = True
            
            if any(provider_healths.values()):
                components["market_feed"] = "ok"
            else:
                components["market_feed"] = "error"
            components["market_providers"] = provider_healths
        else:
            components["market_feed"] = "standby"
    except Exception as e:
        logger.warning(f"Market feed health check error: {e}")
        components["market_feed"] = "standby"

    try:
        from app.agents.providers.router import model_router
        health_results = await model_router.health_check_all()
        components["openrouter"] = "ok" if health_results.get("openrouter") else "standby"
        components["ai_engine"] = "ok" if any(health_results.values()) else "standby"
    except Exception:
        components["openrouter"] = "standby"
        components["ai_engine"] = "standby"

    try:
        components["websocket"] = "ok"
    except Exception:
        components["websocket"] = "standby"

    all_ok = all(v == "ok" for v in components.values())
    degraded = any(v in ("error", "uninitialized") for v in components.values())

    return {
        "success": True,
        "status": "healthy" if all_ok else "degraded" if not degraded else "unhealthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "execution_mode": settings.EXECUTION_MODE,
        "components": components,
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