from app.forecast_engine.base.models import ForecastRequest, ForecastResult
from app.forecast_engine.base.provider import BaseForecastProvider


class ProphetProvider(BaseForecastProvider):
    @property
    def provider_name(self) -> str:
        return "prophet"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def predict(self, request: ForecastRequest) -> ForecastResult:
        """Bollinger Bands model: detects breakout/squeeze using 20-period SMA ± 2 std."""
        if not request.historical_data or len(request.historical_data) < 20:
            return ForecastResult(model_id=self.model_id, direction="NEUTRAL", confidence=0.0, reasoning_metadata={"reason": "insufficient_data"})

        closes = [c.get("close", 0) for c in request.historical_data[-20:]]
        sma = sum(closes) / len(closes)
        std = (sum((c - sma) ** 2 for c in closes) / len(closes)) ** 0.5

        upper = sma + 2 * std
        lower = sma - 2 * std
        current = closes[-1]

        if current <= lower:
            direction = "BULLISH"
            conf = min((lower - current) / std + 0.65, 1.0) if std else 0.65
        elif current >= upper:
            direction = "BEARISH"
            conf = min((current - upper) / std + 0.65, 1.0) if std else 0.65
        else:
            # Position within bands
            band_position = (current - lower) / (upper - lower) if (upper - lower) else 0.5
            if band_position > 0.7:
                direction = "BEARISH"
                conf = 0.55
            elif band_position < 0.3:
                direction = "BULLISH"
                conf = 0.55
            else:
                direction = "NEUTRAL"
                conf = 0.5

        move_pct = abs(current - sma) / sma if sma else 0

        return ForecastResult(
            model_id=self.model_id,
            direction=direction,
            confidence=round(conf, 4),
            probability=round(conf, 4),
            expected_move_pct=round(move_pct, 6),
            reasoning_metadata={"rule": "bollinger_bands", "upper": round(upper, 5), "lower": round(lower, 5), "sma": round(sma, 5)}
        )
