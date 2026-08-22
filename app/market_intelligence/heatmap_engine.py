from typing import Any

from sqlalchemy import select

from app.database.manager import db_manager
from app.database.models.forecast import ForecastConsensusModel, ForecastRequestModel
from app.logs.logger import get_logger

logger = get_logger(__name__)

class HeatmapEngine:
    """
    Aggregates active predictions and market data to produce the Market Heatmap.
    """
    
    async def get_current_heatmap(self) -> dict[str, Any]:
        session_factory = db_manager.get_session()
        if not session_factory:
            return {}

        heatmap = {
            "bullish_assets": [],
            "bearish_assets": [],
            "neutral_assets": [],
            "strong_trend": [],
            "weak_trend": [],
            "high_volatility": [],
            "low_volatility": [],
            "highest_confidence": None,
            "lowest_confidence": None
        }

        async with session_factory() as session:
            stmt = (
                select(ForecastConsensusModel, ForecastRequestModel)
                .join(ForecastRequestModel)
                .where(ForecastConsensusModel.lifecycle_state == "ACTIVE")
            )
            result = await session.execute(stmt)
            rows = result.all()

            all_confidences = []

            for consensus, request in rows:
                sym = request.symbol
                conf = consensus.combined_confidence
                all_confidences.append({"symbol": sym, "confidence": conf})

                if consensus.combined_direction == "BULLISH":
                    if conf > 0.8:
                        heatmap["strong_trend"].append(sym)
                    heatmap["bullish_assets"].append(sym)
                elif consensus.combined_direction == "BEARISH":
                    if conf > 0.8:
                        heatmap["strong_trend"].append(sym)
                    heatmap["bearish_assets"].append(sym)
                else:
                    heatmap["neutral_assets"].append(sym)

            if all_confidences:
                all_confidences.sort(key=lambda x: x["confidence"])
                heatmap["lowest_confidence"] = all_confidences[0]
                heatmap["highest_confidence"] = all_confidences[-1]

        return heatmap

heatmap_engine = HeatmapEngine()
