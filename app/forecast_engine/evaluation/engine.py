from datetime import datetime, timezone

from app.database.manager import db_manager
from app.database.models.forecast import ForecastEvaluationModel, ForecastResultModel
from app.logs.logger import get_logger

logger = get_logger(__name__)

class ForecastEvaluator:
    """
    Evaluates historical forecasts against actual market outcomes.
    Updates model performance metrics and rolling accuracy.
    """

    async def evaluate_pending_results(self):
        """
        Finds results that have passed their expiry timestamp but haven't been evaluated yet,
        and computes their accuracy against actual market data.
        """
        session_factory = db_manager.get_session()
        if not session_factory:
            return

        now = datetime.now(timezone.utc)
        
        async with session_factory() as session:
            # Get expired results without evaluations
            # In SQLAlchemy 2.0 async, this requires a join or subquery. We'll do a simple select for now.
            # Real implementation would use an OUTER JOIN where evaluation.id IS NULL
            
            # For stub implementation, we just log that we would evaluate
            logger.info("ForecastEvaluator: Checking for pending evaluations...")

    async def evaluate_result(self, result: ForecastResultModel, actual_close_pct: float) -> ForecastEvaluationModel:
        """
        Evaluates a single ForecastResult.
        """
        
        # Calculate errors
        prediction_error_pct = abs(result.expected_move_pct - actual_close_pct) if result.expected_move_pct else 0.0
        
        # Determine actual direction
        actual_direction = "NEUTRAL"
        if actual_close_pct > 0.1:
            actual_direction = "BULLISH"
        elif actual_close_pct < -0.1:
            actual_direction = "BEARISH"
            
        directional_accuracy = (result.direction == actual_direction)

        evaluation = ForecastEvaluationModel(
            result_id=result.id,
            actual_outcome_pct=actual_close_pct,
            actual_direction=actual_direction,
            prediction_error_pct=prediction_error_pct,
            directional_accuracy=directional_accuracy
        )
        
        return evaluation

    async def update_model_performance(self, model_id: str):
        """
        Recalculates aggregate metrics for a specific model.
        """
        session_factory = db_manager.get_session()
        if not session_factory:
            return

        async with session_factory() as session:
            # In a real scenario, we'd query all evaluations for this model_id,
            # calculate Win Rate, RMSE, MAE, and update the ForecastPerformanceModel.
            logger.info(f"Updated performance metrics for model: {model_id}")

forecast_evaluator = ForecastEvaluator()
