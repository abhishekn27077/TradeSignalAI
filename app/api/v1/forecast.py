from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.forecast_engine.orchestrator.engine import forecast_orchestrator
from app.forecast_engine.registry.manager import model_registry

router = APIRouter(prefix="/forecast", tags=["Forecast Intelligence"])

class ForecastRequestParams(BaseModel):
    symbol: str
    timeframe: str
    forecast_horizon: int
    market_regime: str = None

@router.post("/run", summary="Execute an on-demand forecast")
async def run_forecast(params: ForecastRequestParams):
    """
    Executes an on-demand forecast across all enabled models and returns the consensus.
    """
    try:
        result = await forecast_orchestrator.run_forecast(
            symbol=params.symbol,
            timeframe=params.timeframe,
            forecast_horizon=params.forecast_horizon,
            market_regime=params.market_regime
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models", summary="List all forecast models")
async def list_models():
    """
    Returns the status and metadata of all registered forecasting models.
    """
    try:
        providers = model_registry.get_all_active_providers()
        return {
            "count": len(providers),
            "models": [
                {
                    "name": p.provider_name,
                    "version": p.version,
                    "status": "active"
                }
                for p in providers
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
