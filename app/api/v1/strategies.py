
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.logs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/strategies", tags=["strategies"])


class StrategyConfigUpdate(BaseModel):
    status: str | None = None
    priority: int | None = None
    weight: float | None = None
    max_concurrent_trades: int | None = None
    daily_trade_limit: int | None = None
    allowed_sessions: list[str] | None = None
    allowed_assets: list[str] | None = None
    allowed_timeframes: list[str] | None = None
    min_trade_quality: int | None = None
    min_ai_confidence: float | None = None


@router.get("", summary="List All Strategies")
async def list_strategies():
    try:
        from app.strategies.manager import strategy_manager
        configs = strategy_manager.get_all_configs()
        return {"success": True, "strategies": configs}
    except Exception as e:
        logger.warning(f"Strategies list error: {e}")
        return {"success": True, "strategies": []}


@router.get("/active", summary="Get Active Strategies")
async def get_active_strategies():
    try:
        from app.strategies.manager import strategy_manager
        configs = strategy_manager.get_all_configs()
        active = [s for s in configs if s.get("status") == "ENABLED"]
        return {"success": True, "strategies": active}
    except Exception as e:
        logger.warning(f"Active strategies error: {e}")
        return {"success": True, "strategies": []}


@router.get("/health", summary="Get Strategy Engine Health")
async def strategy_health():
    try:
        from app.strategies.manager import strategy_manager
        configs = strategy_manager.get_all_configs()
        enabled = len([s for s in configs if s.get("status") == "ENABLED"])
        total = len(configs)
        return {
            "success": True,
            "data": {
                "status": "healthy",
                "total_strategies": total,
                "enabled_strategies": enabled,
                "disabled_strategies": total - enabled,
            }
        }
    except Exception as e:
        logger.warning(f"Strategy health error: {e}")
        return {"success": True, "data": {"status": "unavailable"}}


@router.get("/{strategy_name}", summary="Get Strategy Details")
async def get_strategy(strategy_name: str):
    try:
        from app.strategies.manager import strategy_manager
        from app.strategies.plugins.registry import strategy_registry
        config = strategy_manager.get_config(strategy_name)
        if config is None:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_name} not found")
        meta = strategy_registry.get_metadata(strategy_name)
        return {
            "success": True,
            "strategy": {
                **config,
                "description": meta.description if meta else "",
                "version": meta.version if meta else "",
                "category": meta.category.value if meta else "",
                "entry_rules": meta.entry_rules if meta else [],
                "exit_rules": meta.exit_rules if meta else [],
                "required_indicators": meta.required_indicators if meta else [],
                "supported_regimes": [r.value for r in meta.supported_regimes] if meta else [],
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Get strategy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{strategy_name}/enable", summary="Enable Strategy")
async def enable_strategy(strategy_name: str):
    try:
        from app.strategies.manager import strategy_manager
        result = strategy_manager.enable_strategy(strategy_name)
        return {"success": result, "strategy": strategy_name, "status": "ENABLED"}
    except Exception as e:
        logger.warning(f"Enable strategy error: {e}")
        return {"success": False, "message": str(e)}


@router.post("/{strategy_name}/disable", summary="Disable Strategy")
async def disable_strategy(strategy_name: str):
    try:
        from app.strategies.manager import strategy_manager
        result = strategy_manager.disable_strategy(strategy_name)
        return {"success": result, "strategy": strategy_name, "status": "DISABLED"}
    except Exception as e:
        logger.warning(f"Disable strategy error: {e}")
        return {"success": False, "message": str(e)}


@router.post("/{strategy_name}/pause", summary="Pause Strategy")
async def pause_strategy(strategy_name: str):
    try:
        from app.strategies.manager import strategy_manager
        result = strategy_manager.pause_strategy(strategy_name)
        return {"success": result, "strategy": strategy_name, "status": "PAUSED"}
    except Exception as e:
        logger.warning(f"Pause strategy error: {e}")
        return {"success": False, "message": str(e)}


@router.post("/{strategy_name}/resume", summary="Resume Strategy")
async def resume_strategy(strategy_name: str):
    try:
        from app.strategies.manager import strategy_manager
        result = strategy_manager.resume_strategy(strategy_name)
        return {"success": result, "strategy": strategy_name, "status": "ENABLED"}
    except Exception as e:
        logger.warning(f"Resume strategy error: {e}")
        return {"success": False, "message": str(e)}


@router.put("/{strategy_name}/config", summary="Update Strategy Configuration")
async def update_strategy_config(strategy_name: str, config: StrategyConfigUpdate):
    try:
        from app.strategies.manager import strategy_manager
        update_dict = {k: v for k, v in config.model_dump().items() if v is not None}
        result = strategy_manager.set_config(strategy_name, update_dict)
        if not result:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_name} not found")
        return {"success": True, "strategy": strategy_name, "config": strategy_manager.get_config(strategy_name)}
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Update config error: {e}")
        return {"success": False, "message": str(e)}


@router.post("/{strategy_name}/priority", summary="Set Strategy Priority")
async def set_priority(strategy_name: str, priority: int):
    try:
        from app.strategies.manager import strategy_manager
        result = strategy_manager.set_priority(strategy_name, priority)
        return {"success": result, "strategy": strategy_name, "priority": priority}
    except Exception as e:
        logger.warning(f"Set priority error: {e}")
        return {"success": False, "message": str(e)}


@router.get("/{strategy_name}/analytics", summary="Get Strategy Analytics")
async def get_strategy_analytics(strategy_name: str):
    try:
        from app.strategies.analytics.engine import strategy_analytics_engine
        analytics = strategy_analytics_engine.get_analytics(strategy_name)
        if analytics is None:
            return {"success": True, "analytics": {"strategy_name": strategy_name, "total_trades": 0}}
        return {"success": True, "analytics": analytics.to_dict()}
    except Exception as e:
        logger.warning(f"Get analytics error: {e}")
        return {"success": False, "message": str(e)}


@router.get("/{strategy_name}/optimize", summary="Get Strategy Optimization Recommendations")
async def optimize_strategy(strategy_name: str):
    try:
        from app.strategies.analytics.engine import strategy_analytics_engine
        from app.strategies.manager import strategy_manager
        from app.strategies.optimizer import strategy_optimizer
        analytics = strategy_analytics_engine.get_analytics(strategy_name)
        config = strategy_manager.get_config(strategy_name)
        if analytics is None:
            return {"success": True, "recommendations": []}
        result = strategy_optimizer.analyze(analytics.to_dict(), config)
        return {"success": True, "recommendations": result.to_dict()}
    except Exception as e:
        logger.warning(f"Optimize error: {e}")
        return {"success": False, "message": str(e)}


@router.get("/optimize/all", summary="Get All Strategy Optimization Recommendations")
async def optimize_all_strategies():
    try:
        from app.strategies.analytics.engine import strategy_analytics_engine
        from app.strategies.optimizer import strategy_optimizer
        all_a = strategy_analytics_engine.get_all_analytics_dict()
        results = strategy_optimizer.analyze_all(all_a)
        return {"success": True, "recommendations": results}
    except Exception as e:
        logger.warning(f"Optimize all error: {e}")
        return {"success": False, "message": str(e)}


