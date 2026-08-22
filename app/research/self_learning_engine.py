from typing import Any

from sqlalchemy.future import select

from app.database.manager import db_manager
from app.database.models.forecast import ForecastModelMetadata
from app.logs.logger import get_logger
from app.utils.event_bus import event_bus

logger = get_logger(__name__)

class SelfLearningEngine:
    """
    Updates model calibration weights based on recent performance.
    Listens to 'ForecastEvaluated' events.
    """
    def __init__(self):
        self.is_running = False

    async def start(self):
        self.is_running = True
        event_bus.subscribe("ForecastEvaluated", self.handle_evaluation)
        logger.info("SelfLearningEngine started")

    async def stop(self):
        self.is_running = False
        logger.info("SelfLearningEngine stopped")

    async def handle_evaluation(self, payload: dict[str, Any]):
        """
        Update the model rankings and confidence calibrations.
        """
        validation_id = payload.get("validation_id")
        pnl_pct = payload.get("pnl_pct", 0.0)
        direction_correct = payload.get("direction_correct", False)
        
        logger.info(f"Self-learning triggered for validation: {validation_id}, PnL: {pnl_pct}%")
        
        # This represents Phase 12 - Self Learning.
        # We adjust the priority (weight) of the models that contributed to this forecast.
        # In this simplified implementation, we'll boost priority of enabled models if the overall consensus was right,
        # and penalize if it was wrong. (A real implementation would look up the specific model contributions)
        
        session_factory = db_manager.get_session()
        async with session_factory() as session:
            stmt = select(ForecastModelMetadata).where(ForecastModelMetadata.is_enabled == True)
            result = await session.execute(stmt)
            models = result.scalars().all()
            
            for model in models:
                # If direction was correct and PnL > 0, boost priority (lower number = higher priority, or higher number = higher weight depending on engine)
                # We'll assume priority is a ranking (1 is best).
                if direction_correct:
                    # Slightly improve priority
                    if model.priority > 1:
                        model.priority -= 1 
                else:
                    # Penalize
                    model.priority += 1
                
            await session.commit()
            logger.info("SelfLearningEngine adjusted model priorities based on recent outcome.")

self_learning_engine = SelfLearningEngine()
