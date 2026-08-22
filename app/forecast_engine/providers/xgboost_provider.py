import numpy as np
import xgboost as xgb

from app.forecast_engine.base.models import ForecastRequest, ForecastResult
from app.forecast_engine.base.provider import BaseForecastProvider


class XGBoostProvider(BaseForecastProvider):
    @property
    def provider_name(self) -> str:
        return "xgboost"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def predict(self, request: ForecastRequest) -> ForecastResult:
        """Real XGBoost model trained on the fly on recent historical data."""
        if not request.historical_data or len(request.historical_data) < 50:
            return ForecastResult(model_id=self.model_id, direction="NEUTRAL", confidence=0.0, reasoning_metadata={"reason": "insufficient_data"})

        data = request.historical_data
        
        # Build features and labels
        # Target: 1 if close in T+1 is > close in T, else 0
        features = []
        labels = []
        
        for i in range(10, len(data) - 1):
            window = data[i-10:i]
            # Feature extraction: rolling returns and volatility
            window_closes = [w.get("close", 0) for w in window]
            window_returns = [ (window_closes[j] - window_closes[j-1])/window_closes[j-1] if window_closes[j-1] else 0 for j in range(1, len(window_closes)) ]
            
            feat = [
                np.mean(window_returns),
                np.std(window_returns),
                window_closes[-1] / window_closes[0] - 1,
                np.max(window_closes) / window_closes[-1] - 1,
                np.min(window_closes) / window_closes[-1] - 1
            ]
            features.append(feat)
            
            # Label
            next_close = data[i+1].get("close", 0)
            curr_close = window_closes[-1]
            labels.append(1 if next_close > curr_close else 0)

        X = np.array(features)
        y = np.array(labels)
        
        if len(np.unique(y)) < 2:
            return ForecastResult(model_id=self.model_id, direction="NEUTRAL", confidence=0.0, reasoning_metadata={"reason": "one_class_target"})

        # Train a small fast XGBoost classifier
        model = xgb.XGBClassifier(n_estimators=20, max_depth=3, learning_rate=0.1, use_label_encoder=False, eval_metric='logloss')
        model.fit(X, y)

        # Predict next step
        recent_window = data[-10:]
        recent_closes = [w.get("close", 0) for w in recent_window]
        recent_returns = [ (recent_closes[j] - recent_closes[j-1])/recent_closes[j-1] if recent_closes[j-1] else 0 for j in range(1, len(recent_closes)) ]
        
        X_test = np.array([[
            np.mean(recent_returns),
            np.std(recent_returns),
            recent_closes[-1] / recent_closes[0] - 1,
            np.max(recent_closes) / recent_closes[-1] - 1,
            np.min(recent_closes) / recent_closes[-1] - 1
        ]])
        
        prob = model.predict_proba(X_test)[0]
        prob_up = prob[1]
        prob_down = prob[0]
        
        if prob_up > 0.55:
            direction = "BULLISH"
            conf = prob_up
        elif prob_down > 0.55:
            direction = "BEARISH"
            conf = prob_down
        else:
            direction = "NEUTRAL"
            conf = max(prob_up, prob_down)
            
        move_pct = abs(np.mean(recent_returns))
            
        return ForecastResult(
            model_id=self.model_id,
            direction=direction,
            confidence=round(float(conf), 4),
            probability=round(float(conf), 4),
            expected_move_pct=round(float(move_pct), 6),
            reasoning_metadata={"rule": "xgboost_rolling", "prob_up": float(prob_up), "prob_down": float(prob_down)}
        )
