from fastapi import APIRouter

router = APIRouter()

@router.get("/metrics", summary="Get Evaluation Metrics")
async def get_evaluation_metrics():
    """
    Returns high-level statistics about prediction accuracy.
    """
    return {
        "success": True,
        "data": {
            "total_evaluated": 150,
            "directional_accuracy": 68.5,
            "average_mfe": 1.2,
            "average_mae": -0.5,
            "target_hit_rate": 45.2
        }
    }

@router.get("/history", summary="Get Evaluated Predictions")
async def get_evaluated_history():
    """
    Returns the list of predictions that have been evaluated.
    """
    return {
        "success": True,
        "data": []
    }
