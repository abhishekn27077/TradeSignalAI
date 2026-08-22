from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)


class ExposureManager:
    def __init__(self):
        self._exposures: dict[str, dict[str, Any]] = {}

    def set_exposure(self, symbol: str, direction: str, quantity: float, price: float):
        self._exposures[symbol] = {
            "symbol": symbol,
            "direction": direction,
            "quantity": quantity,
            "price": price,
            "exposure_value": quantity * price,
        }

    def get_exposure(self) -> dict[str, Any]:
        total = sum(e.get("exposure_value", 0) for e in self._exposures.values())
        return {
            "total_exposure": total,
            "positions": list(self._exposures.values()),
        }

    def calculate_exposure(self, positions: list[dict]) -> dict[str, Any]:
        gross_exposure = 0.0
        net_exposure = 0.0
        for pos in positions:
            value = pos.get("quantity", 0) * pos.get("current_price", 0)
            gross_exposure += value
            if pos.get("direction", "BUY").upper() == "BUY":
                net_exposure += value
            else:
                net_exposure -= value
        
        return {
            "gross_exposure": gross_exposure,
            "net_exposure": net_exposure
        }


exposure_manager = ExposureManager()