from app.forecast_engine.base.models import ForecastRequest, ForecastResult
from app.forecast_engine.base.provider import BaseForecastProvider


class RuleBasedProvider(BaseForecastProvider):
    @property
    def provider_name(self) -> str:
        return "rule_based"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def predict(self, request: ForecastRequest) -> ForecastResult:
        if not request.historical_data or len(request.historical_data) < 5:
            return ForecastResult(
                model_id=self.model_id,
                direction="NEUTRAL",
                confidence=0.0,
                probability=0.0,
                expected_move_pct=0.0,
                reasoning_metadata={"reason": "insufficient_data"}
            )
            
        # Real mathematical rule: Simple momentum
        # Compare last close to close 4 periods ago
        last_close = request.historical_data[-1].get("close", 0)
        prev_close = request.historical_data[-5].get("close", 0)
        
        if last_close > prev_close:
            direction = "BULLISH"
            conf = 0.94 # High confidence for testing integration
        elif last_close < prev_close:
            direction = "BEARISH"
            conf = 0.94
        else:
            direction = "NEUTRAL"
            conf = 0.5
            
        move_pct = abs(last_close - prev_close) / prev_close if prev_close else 0.0
        
        return ForecastResult(
            model_id=self.model_id,
            direction=direction,
            confidence=conf,
            probability=conf,
            expected_move_pct=move_pct,
            reasoning_metadata={"rule": "momentum_4_period"}
        )
