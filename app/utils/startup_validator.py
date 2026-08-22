from typing import Any

from sqlalchemy import text

from app.config.settings import get_settings
from app.database.manager import db_manager
from app.logs.logger import get_logger

logger = get_logger(__name__)

class StartupValidator:
    def __init__(self):
        self.settings = get_settings()

    async def validate_all(self) -> dict[str, Any]:
        logger.info("Executing System Startup Validation...")
        results = {}
        critical_failed = False

        results["database"] = await self._check_database()
        if not results["database"]["healthy"]:
            critical_failed = True

        results["execution_mode"] = {
            "healthy": True,
            "mode": self.settings.EXECUTION_MODE,
            "auto_trading": self.settings.AUTO_TRADING_ENABLED,
            "kill_switch": self.settings.EMERGENCY_KILL_SWITCH,
        }
        if self.settings.EMERGENCY_KILL_SWITCH:
            logger.warning("ATTENTION: Emergency Kill Switch is currently ACTIVE!")

        results["openrouter"] = await self._check_openrouter()
        results["tradingview"] = self._check_tradingview_config()

        for service, status in results.items():
            state = "HEALTHY" if status.get("healthy", True) else "UNHEALTHY"
            logger.info(f"Startup Check -> [{service.upper()}]: {state}")

        if critical_failed:
            logger.warning("Some critical services failed validation. Starting in DEGRADED mode.")

        logger.info("System Startup Validation Complete.")
        return results

    async def _check_database(self) -> dict[str, Any]:
        try:
            if db_manager._engine:
                async with db_manager._engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                return {"healthy": True, "details": "Database connection verified."}
            else:
                return {"healthy": False, "details": "Database engine not initialized."}
        except Exception as e:
            logger.warning(f"Database ping failed: {e}")
            return {"healthy": False, "details": f"Database ping failed: {e}"}

    async def _check_openrouter(self) -> dict[str, Any]:
        try:
            from app.agents.providers.router import model_router
            healthy_map = await model_router.health_check_all()
            if healthy_map.get("openrouter", False) or healthy_map.get("openai", False):
                return {"healthy": True, "details": "AI Provider(s) verified"}
            return {"healthy": False, "details": "All AI Providers failed health check"}
        except Exception as e:
            return {"healthy": False, "details": f"AI provider check failed: {e}"}

    def _check_tradingview_config(self) -> dict[str, Any]:
        if self.settings.TV_USERNAME:
            return {"healthy": True, "details": f"TradingView Account {self.settings.TV_USERNAME} configured."}
        return {"healthy": True, "details": "TradingView not fully configured (running in guest/simulated mode)."}

startup_validator = StartupValidator()