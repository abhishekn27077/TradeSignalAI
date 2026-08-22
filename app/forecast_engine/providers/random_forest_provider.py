import numpy as np
from sklearn.ensemble import RandomForestClassifier

from app.forecast_engine.base.models import ForecastRequest, ForecastResult
from app.forecast_engine.base.provider import BaseForecastProvider


class RandomForestProvider(BaseForecastProvider):
    @property
    def provider_name(self) -> str:
        return "random_forest"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def predict(self, request: ForecastRequest) -> ForecastResult:
        """Real Random Forest model trained on the fly on recent historical data."""
        if not request.historical_data or len(request.historical_data) < 50:
            return ForecastResult(model_id=self.model_id, direction="NEUTRAL", confidence=0.0, reasoning_metadata={"reason": "insufficient_data"})

        data = request.historical_data
        
        # Build features and labels
        # Target: 1 if close in T+1 is > close in T, else 0
        features = []
        labels = []
        
        for i in range(14, len(data) - 1):
            window = data[i-14:i]
            window_closes = [w.get("close", 0) for w in window]
            window_volumes = [w.get("volume", 0) for w in window]
            
            # Simple momentum features
            mom_3 = window_closes[-1] / window_closes[-3] - 1 if window_closes[-3] else 0
            mom_7 = window_closes[-1] / window_closes[-7] - 1 if window_closes[-7] else 0
            mom_14 = window_closes[-1] / window_closes[-14] - 1 if window_closes[-14] else 0
            
            vol_avg = np.mean(window_volumes)
            vol_ratio = window_volumes[-1] / vol_avg if vol_avg else 1.0
            
            feat = [mom_3, mom_7, mom_14, vol_ratio]
            features.append(feat)
            
            # Label
            next_close = data[i+1].get("close", 0)
            curr_close = window_closes[-1]
            labels.append(1 if next_close > curr_close else 0)

        X = np.array(features)
        y = np.array(labels)
        
        if len(np.unique(y)) < 2:
            return ForecastResult(model_id=self.model_id, direction="NEUTRAL", confidence=0.0, reasoning_metadata={"reason": "one_class_target"})

        model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        model.fit(X, y)

        recent_window = data[-14:]
        recent_closes = [w.get("close", 0) for w in recent_window]
        recent_volumes = [w.get("volume", 0) for w in recent_window]
        
        mom_3_curr = recent_closes[-1] / recent_closes[-3] - 1 if recent_closes[-3] else 0
        mom_7_curr = recent_closes[-1] / recent_closes[-7] - 1 if recent_closes[-7] else 0
        mom_14_curr = recent_closes[-1] / recent_closes[-14] - 1 if recent_closes[-14] else 0
        
        vol_avg_curr = np.mean(recent_volumes)
        vol_ratio_curr = recent_volumes[-1] / vol_avg_curr if vol_avg_curr else 1.0
        
        X_test = np.array([[mom_3_curr, mom_7_curr, mom_14_curr, vol_ratio_curr]])
        
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
            
        return ForecastResult(
            model_id=self.model_id,
            direction=direction,
            confidence=round(float(conf), 4),
            probability=round(float(conf), 4),
            expected_move_pct=abs(float(mom_3_curr)),
            reasoning_metadata={"rule": "random_forest_rolling", "prob_up": float(prob_up), "prob_down": float(prob_down)}
        )
