from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ExperimentRequest(BaseModel):
    name: str
    horizon: int
    confidence_threshold: float
    features: list

@router.post("/run", summary="Run Hyperparameter Experiment")
async def run_experiment(req: ExperimentRequest):
    """
    Runs a backtest simulation using modified hyperparameters.
    """
    # Stub
    return {
        "success": True,
        "data": {
            "experiment_id": "exp-123",
            "results": {
                "accuracy": 71.2,
                "profit_factor": 1.5
            }
        }
    }

@router.get("/history", summary="Get Experiment History")
async def get_experiment_history():
    return {
        "success": True,
        "data": []
    }
