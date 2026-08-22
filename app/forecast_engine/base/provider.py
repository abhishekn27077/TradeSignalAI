from abc import ABC, abstractmethod
from typing import Any

from app.forecast_engine.base.models import ForecastRequest, ForecastResult


class BaseForecastProvider(ABC):
    """
    The Base Forecast Provider interface.
    Every forecasting model (Kronos, LSTM, XGBoost, etc.) MUST implement this interface.
    """
    
    def __init__(self, model_id: str, config: dict[str, Any] | None = None):
        self.model_id = model_id
        self.config = config or {}

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the unique name of this provider (e.g., 'kronos', 'lstm')."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Return the version of this provider."""

    async def initialize(self) -> bool:
        """
        Optional initialization logic (loading weights, connecting to inference server).
        Returns True if successful, False otherwise.
        """
        return True

    @abstractmethod
    async def predict(self, request: ForecastRequest) -> ForecastResult:
        """
        Execute the forecast prediction logic.
        
        :param request: The standardized ForecastRequest containing symbol, timeframe, horizon, and historical/feature data.
        :return: A standardized ForecastResult.
        :raises NotImplementedError: If the model is a stub and not yet fully implemented.
        """

    async def shutdown(self):
        """Optional shutdown cleanup logic."""
