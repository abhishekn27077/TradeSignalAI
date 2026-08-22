from app.forecast_engine.base.models import ForecastRequest, ForecastResult
from app.forecast_engine.base.provider import BaseForecastProvider


class TransformerProvider(BaseForecastProvider):
    @property
    def provider_name(self) -> str:
        return "transformer"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def predict(self, request: ForecastRequest) -> ForecastResult:
        """EMA crossover model: compares fast EMA(5) vs slow EMA(20)."""
        if not request.historical_data or len(request.historical_data) < 20:
            return ForecastResult(model_id=self.model_id, direction="NEUTRAL", confidence=0.0, reasoning_metadata={"reason": "insufficient_data"})

        closes = [c.get("close", 0) for c in request.historical_data]

        def ema(data, period):
            k = 2 / (period + 1)
            result = data[0]
            for price in data[1:]:
                result = price * k + result * (1 - k)
            return result

        ema_fast = ema(closes[-10:], 5)
        ema_slow = ema(closes[-20:], 20)

        if ema_fast > ema_slow:
            direction = "BULLISH"
        elif ema_fast < ema_slow:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"

        spread = abs(ema_fast - ema_slow) / ema_slow if ema_slow else 0
        conf = min(spread * 100, 1.0)  # scale spread to confidence
        conf = max(conf, 0.55) if direction != "NEUTRAL" else 0.5

        return ForecastResult(
            model_id=self.model_id,
            direction=direction,
            confidence=round(conf, 4),
            probability=round(conf, 4),
            expected_move_pct=round(spread, 6),
            reasoning_metadata={"rule": "ema_crossover", "ema_fast": round(ema_fast, 5), "ema_slow": round(ema_slow, 5)}
        )
