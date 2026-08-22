from app.forecast_engine.base.models import ForecastRequest, ForecastResult
from app.forecast_engine.base.provider import BaseForecastProvider


class KronosProvider(BaseForecastProvider):
    @property
    def provider_name(self) -> str:
        return "kronos"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def predict(self, request: ForecastRequest) -> ForecastResult:
        """RSI-based model: detects overbought/oversold conditions using 14-period RSI."""
        if not request.historical_data or len(request.historical_data) < 15:
            return ForecastResult(model_id=self.model_id, direction="NEUTRAL", confidence=0.0, reasoning_metadata={"reason": "insufficient_data"})

        # Convert historical data to standard dataframe and run prediction
        try:
            closes = [c.get("close", 0) for c in request.historical_data[-15:]]
            
            from app.analytics.models.kronos.adapter import KronosAdapter
            adapter = KronosAdapter(device="cpu")
            df = adapter.format_market_data(request.historical_data)
            
            # Request 5 steps forward
            pred_df = adapter.predict(df, pred_len=5)
            
            last_close = closes[-1]
            future_close = pred_df['close'].iloc[-1] if not pred_df.empty else last_close
            
            move_pct = (future_close - last_close) / last_close if last_close != 0 else 0.0
            
            if move_pct > 0.001:
                direction = "BULLISH"
                conf = min(0.5 + (move_pct * 10), 1.0)
            elif move_pct < -0.001:
                direction = "BEARISH"
                conf = min(0.5 + (abs(move_pct) * 10), 1.0)
            else:
                direction = "NEUTRAL"
                conf = 0.5
                
            return ForecastResult(
                model_id=self.model_id,
                direction=direction,
                confidence=round(conf, 4),
                probability=round(conf, 4),
                expected_move_pct=round(move_pct, 6),
                reasoning_metadata={
                    "rule": "kronos_time_series", 
                    "pred_len": 5,
                    "target_close": float(future_close)
                }
            )
        except Exception as e:
            return ForecastResult(
                model_id=self.model_id, 
                direction="NEUTRAL", 
                confidence=0.0, 
                reasoning_metadata={"error": str(e)}
            )
