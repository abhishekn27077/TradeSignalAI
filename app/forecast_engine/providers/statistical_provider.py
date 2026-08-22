from app.forecast_engine.base.models import ForecastRequest, ForecastResult
from app.forecast_engine.base.provider import BaseForecastProvider


class StatisticalProvider(BaseForecastProvider):
    @property
    def provider_name(self) -> str:
        return "statistical"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def predict(self, request: ForecastRequest) -> ForecastResult:
        """Mean-reversion z-score model: compares current price to rolling mean."""
        if not request.historical_data or len(request.historical_data) < 20:
            return ForecastResult(model_id=self.model_id, direction="NEUTRAL", confidence=0.0, reasoning_metadata={"reason": "insufficient_data"})

        closes = [c.get("close", 0) for c in request.historical_data[-20:]]
        mean = sum(closes) / len(closes)
        std = (sum((c - mean) ** 2 for c in closes) / len(closes)) ** 0.5
        if std == 0:
            return ForecastResult(model_id=self.model_id, direction="NEUTRAL", confidence=0.5, reasoning_metadata={"rule": "zero_std"})

        z_score = (closes[-1] - mean) / std

        if z_score < -1.0:
            direction = "BULLISH"  # oversold, expect reversion up
        elif z_score > 1.0:
            direction = "BEARISH"  # overbought, expect reversion down
        else:
            direction = "NEUTRAL"

        conf = min(abs(z_score) / 3.0, 1.0)
        move_pct = abs(closes[-1] - mean) / mean if mean else 0.0

        return ForecastResult(
            model_id=self.model_id,
            direction=direction,
            confidence=round(conf, 4),
            probability=round(conf, 4),
            expected_move_pct=round(move_pct, 6),
            reasoning_metadata={"rule": "z_score_mean_reversion", "z_score": round(z_score, 4)}
        )
