
from fastapi import APIRouter, Query

from app.logs.logger import get_logger
from app.validation.engine import validation_engine

logger = get_logger(__name__)

router = APIRouter(prefix="/validation", tags=["validation"])

@router.get("/reports")
async def get_validation_reports(period: str = Query(default="all")):
    """
    Returns research validation metrics like Accuracy, Precision, Recall, Win Rate,
    Sharpe Ratio, Max Drawdown, MAE, RMSE, etc.
    """
    try:
        metrics = await validation_engine.compute_metrics(period)
        return {"success": True, "period": period, "metrics": metrics}
    except Exception as e:
        logger.error(f"Error fetching validation reports: {e}")
        return {"success": False, "error": str(e)}

@router.get("/rankings")
async def get_validation_rankings(period: str = Query(default="all")):
    """
    Returns rankings for strategies, models, assets, timeframes, and sessions.
    """
    try:
        rankings = await validation_engine.get_rankings(period)
        return {"success": True, "period": period, "rankings": rankings}
    except Exception as e:
        logger.error(f"Error fetching validation rankings: {e}")
        return {"success": False, "error": str(e)}
