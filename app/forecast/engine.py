from abc import ABC, abstractmethod
from typing import Any


class BaseForecastModel(ABC):
    """
    Abstract base class for all forecasting models.
    """
    def __init__(self, model_id: str, name: str):
        self.model_id = model_id
        self.name = name

    @abstractmethod
    def predict(self, symbol: str, timeframe: str, features: dict[str, Any]) -> dict[str, Any]:
        """
        Generate a prediction based on features.
        Must return a dict containing:
        - direction: 'BUY' or 'SELL'
        - confidence: float 0.0-1.0
        - expected_move_pct: float
        - expected_hold_time_hours: float
        - target_price: float
        - stop_price: float
        """

class TransformerModel(BaseForecastModel):
    def __init__(self):
        super().__init__("transformer_v1", "Temporal Transformer")
        
    def predict(self, symbol, timeframe, features):
        # Mock prediction for architecture scaffolding
        return {
            "direction": "BUY",
            "confidence": 0.855,
            "expected_move_pct": 1.2,
            "expected_hold_time_hours": 4.0,
            "target_price": features.get("close", 1.0) * 1.012,
            "stop_price": features.get("close", 1.0) * 0.995,
        }

class XGBoostModel(BaseForecastModel):
    def __init__(self):
        super().__init__("xgb_v1", "XGBoost Classifier")
        
    def predict(self, symbol, timeframe, features):
        return {
            "direction": "SELL",
            "confidence": 0.78,
            "expected_move_pct": -0.8,
            "expected_hold_time_hours": 2.0,
            "target_price": features.get("close", 1.0) * 0.992,
            "stop_price": features.get("close", 1.0) * 1.005,
        }

class ForecastEngine:
    """
    Manages the execution of multiple independent forecast models.
    """
    def __init__(self):
        self.models: list[BaseForecastModel] = [
            TransformerModel(),
            XGBoostModel()
            # Add LSTM, Prophet, Kronos here
        ]
        
    def run_all_models(self, symbol: str, timeframe: str, features: dict[str, Any]) -> list[dict[str, Any]]:
        from app.market_data.registry import asset_registry
        from datetime import datetime, timezone
        
        # Check if the market is open for this asset
        if not asset_registry.is_market_open(symbol, datetime.now(timezone.utc)):
            import logging
            logging.getLogger(__name__).info(f"Market is closed for {symbol}, blocking forecast generation.")
            return []
            
        predictions = []
        for model in self.models:
            try:
                pred = model.predict(symbol, timeframe, features)
                pred["model_id"] = model.model_id
                pred["model_name"] = model.name
                predictions.append(pred)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Model {model.model_id} failed: {e}")
        return predictions
