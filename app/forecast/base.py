from abc import ABC, abstractmethod
from typing import Any


class ForecastModel(ABC):
    """
    Abstract interface for future predictive models (Kronos, LSTM, Transformer, XGBoost, Prophet).
    Allows plugging predictive logic into the system without changing existing architecture.
    """
    
    @abstractmethod
    def predict(self, current_data: dict[str, Any]) -> str:
        """
        Returns a predicted state or direction (e.g., 'UP', 'DOWN', 'RANGE').
        """
        
    @abstractmethod
    def get_confidence(self) -> float:
        """
        Returns the statistical confidence of the prediction (0.0 to 1.0).
        """
        
    @abstractmethod
    def get_horizon(self) -> int:
        """
        Returns the time horizon for the prediction (e.g., number of bars).
        """
