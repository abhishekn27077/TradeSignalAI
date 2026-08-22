from fastapi import APIRouter

router = APIRouter()

@router.get("/leaderboard", summary="Get Model Leaderboard")
async def get_model_leaderboard():
    """
    Returns ranking of all forecasting models based on their historical accuracy.
    """
    # Stub: Return mock leaderboard
    return {
        "success": True,
        "data": [
            {"model_id": "kronos", "rank": 1, "accuracy": 72.5, "consistency": 85.0, "profitability": 1.8},
            {"model_id": "transformer", "rank": 2, "accuracy": 68.2, "consistency": 78.0, "profitability": 1.4},
            {"model_id": "lstm", "rank": 3, "accuracy": 65.1, "consistency": 70.0, "profitability": 1.1},
            {"model_id": "xgboost", "rank": 4, "accuracy": 60.5, "consistency": 65.0, "profitability": 0.9}
        ]
    }

@router.get("/comparison", summary="Compare Specific Models")
async def compare_models(models: str):
    """
    Compares metrics of comma-separated models.
    """
    # Stub: Return comparison data
    return {
        "success": True,
        "data": {
            "kronos": {"accuracy": 72.5, "sharpe": 1.8},
            "transformer": {"accuracy": 68.2, "sharpe": 1.4}
        }
    }
