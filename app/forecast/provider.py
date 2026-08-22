from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Forecast:
    symbol: str = ""
    timeframe: str = "4H"
    direction: str = "WAIT"
    confidence: float = 0.0
    price_target: float | None = None
    stop_level: float | None = None
    expected_move_pct: float = 0.0
    expected_holding_hours: float = 0.0
    model_name: str = "unknown"
    features_used: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "direction": self.direction,
            "confidence": round(self.confidence, 2),
            "price_target": self.price_target,
            "stop_level": self.stop_level,
            "expected_move_pct": round(self.expected_move_pct, 2),
            "expected_holding_hours": round(self.expected_holding_hours, 1),
            "model_name": self.model_name,
            "features_used": self.features_used,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class ForecastProvider(ABC):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def predict(self, symbol: str, timeframe: str, data: Any) -> Forecast | None:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass


class ForecastManager:
    def __init__(self):
        self._providers: dict[str, ForecastProvider] = {}
        self._forecasts: dict[str, list[Forecast]] = {}

    def register(self, provider: ForecastProvider):
        self._providers[provider.name()] = provider
        logger.info(f"Forecast provider registered: {provider.name()}")

    def unregister(self, name: str):
        self._providers.pop(name, None)

    def get_provider(self, name: str) -> ForecastProvider | None:
        return self._providers.get(name)

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())

    def get_forecasts(self, symbol: str = "", provider: str = "") -> list[Forecast]:
        results = []
        for pname, plist in self._forecasts.items():
            if provider and pname != provider:
                continue
            for f in plist:
                if symbol and f.symbol != symbol:
                    continue
                results.append(f)
        return results


forecast_manager = ForecastManager()
