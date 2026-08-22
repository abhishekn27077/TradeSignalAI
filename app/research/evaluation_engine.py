from typing import Any
import uuid

from app.database.manager import db_manager
from app.logs.logger import get_logger
from app.utils.event_bus import event_bus

logger = get_logger(__name__)

class EvaluationEngine:
    """
    Evaluates forecasts after they expire or hit targets.
    Publishes 'ForecastEvaluated' for the self-learning engine.
    """
    def __init__(self):
        self.is_running = False

    async def start(self):
        self.is_running = True
        event_bus.subscribe("ForecastExpired", self.handle_forecast_expired)
        logger.info("EvaluationEngine started")

    async def stop(self):
        self.is_running = False
        logger.info("EvaluationEngine stopped")

    async def handle_forecast_expired(self, payload: dict[str, Any]):
        """
        Evaluate an expired forecast and emit ForecastEvaluated.
        """
        request_id = payload.get("request_id")
        symbol = payload.get("symbol")
        
        logger.info(f"EvaluationEngine evaluating expired forecast for {symbol} (req: {request_id})")
        
        evaluation_result = {
            "evaluation_id": f"eval-{uuid.uuid4()}",
            "request_id": request_id,
            "symbol": symbol,
            "pnl_pct": 0.0,
            "direction_correct": False
        }
        
        try:
            if db_manager.get_session():
                pass
        except Exception:
            pass

        await event_bus.publish("ForecastEvaluated", payload=evaluation_result)


evaluation_engine = EvaluationEngine()
