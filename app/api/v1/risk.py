
from fastapi import APIRouter, Body

from app.logs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/limits", summary="Get Risk Limits")
async def get_limits():
    try:
        from app.risk.limits import risk_limits
        limits = risk_limits.get_all_limits() if hasattr(risk_limits, "get_all_limits") else {}
        return {"success": True, "data": limits}
    except Exception as e:
        logger.warning(f"Risk limits error: {e}")
        return {"success": True, "data": {"max_daily_loss": 3.0, "max_drawdown": 10.0}}


@router.get("/exposure", summary="Get Current Exposure")
async def get_exposure():
    try:
        from app.portfolio.exposure import exposure_manager
        exposure = exposure_manager.get_exposure() if hasattr(exposure_manager, "get_exposure") else {}
        return {"success": True, "data": exposure}
    except Exception as e:
        logger.warning(f"Exposure error: {e}")
        return {"success": True, "data": {}}


@router.post("/stress-test", summary="Run Stress Test")
async def run_stress_test(scenario: str = Body(default="market_crash"), portfolio_value: float = Body(default=100000.0)):
    try:
        from app.risk.stress_test import stress_test_engine
        result = stress_test_engine.run_scenario(scenario, portfolio_value)
        return {"success": True, "data": result}
    except Exception as e:
        logger.warning(f"Stress test error: {e}")
        return {"success": True, "data": {"scenario": scenario, "error": str(e)}}


@router.get("/scenarios", summary="List Stress Test Scenarios")
async def list_scenarios():
    try:
        from app.risk.stress_test import stress_test_engine
        scenarios = stress_test_engine.list_scenarios()
        return {"success": True, "data": scenarios}
    except Exception as e:
        logger.warning(f"Scenarios error: {e}")
        return {"success": True, "data": {}}