from typing import Any

from sqlalchemy import select

from app.database.manager import db_manager
from app.database.models.forecast import ForecastConsensusModel, ForecastRequestModel
from app.logs.logger import get_logger

logger = get_logger(__name__)

class OpportunityRanker:
    """
    Ranks active forecasts across the platform.
    Phase 9: Signal Quality Engine integrated here.
    """

    async def get_ranked_opportunities(self, limit: int = 50) -> list[dict[str, Any]]:
        session_factory = db_manager.get_session()
        if not session_factory:
            return []

        ranked_results = []
        async with session_factory() as session:
            # Get all ACTIVE consensus models
            stmt = (
                select(ForecastConsensusModel, ForecastRequestModel)
                .join(ForecastRequestModel, ForecastConsensusModel.request_id == ForecastRequestModel.id)
                .where(ForecastConsensusModel.lifecycle_state == "ACTIVE")
            )
            
            result = await session.execute(stmt)
            rows = result.all()

            for consensus, request in rows:
                if consensus.combined_direction == "NEUTRAL":
                    continue
                    
                # Signal Quality Engine (Phase 9)
                # Reject weak signals based on confidence threshold and minimum probability
                if consensus.combined_confidence < 60.0 or consensus.combined_probability < 0.6:
                    # Weak signal rejected
                    continue
                    
                # A robust ranking score incorporating confidence and historical weighting
                score = (consensus.combined_confidence * 0.7) + (consensus.combined_probability * 100 * 0.3)

                ranked_results.append({
                    "symbol": request.symbol,
                    "timeframe": request.timeframe,
                    "direction": consensus.combined_direction,
                    "confidence": consensus.combined_confidence,
                    "probability": consensus.combined_probability,
                    "score": score,
                    "request_id": request.id,
                    "created_at": consensus.created_at
                })

        # Sort descending by score
        ranked_results.sort(key=lambda x: x["score"], reverse=True)
        return ranked_results[:limit]

opportunity_ranker = OpportunityRanker()
