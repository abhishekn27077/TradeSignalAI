from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)


class AIReviewer:
    async def review_trade(self, trade: dict[str, Any]) -> dict[str, Any]:
        review_id = trade.get("id", "unknown")
        try:
            from app.agents.providers.router import model_router
            prompt = (
                f"Review this trade:\n"
                f"Symbol: {trade.get('symbol')}\n"
                f"Direction: {trade.get('direction')}\n"
                f"Quantity: {trade.get('quantity')}\n"
                f"Entry Price: {trade.get('price')}\n"
                f"PnL: {trade.get('pnl')}\n"
                f"Strategy: {trade.get('strategy')}\n\n"
                f"Provide: 1. What went well 2. What could improve 3. Risk management assessment 4. Score (1-10)"
            )
            response = await model_router.generate(prompt=prompt)
            if response:
                return {"trade_id": review_id, "review": response, "status": "completed"}
            return {"trade_id": review_id, "review": "AI review unavailable", "status": "unavailable"}
        except Exception as e:
            logger.warning(f"AI review failed for trade {review_id}: {e}")
            return {"trade_id": review_id, "review": "AI review failed", "status": "unavailable"}


ai_reviewer = AIReviewer()