from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)


class ExitManager:
    def __init__(self):
        self._take_profits: dict[str, float] = {}
        self._stop_losses: dict[str, float] = {}

    def set_take_profit(self, symbol: str, price: float):
        self._take_profits[symbol] = price

    def set_stop_loss(self, symbol: str, price: float):
        self._stop_losses[symbol] = price

    def check_exit(self, symbol: str, current_price: float) -> dict[str, Any] | None:
        tp = self._take_profits.get(symbol)
        sl = self._stop_losses.get(symbol)
        if tp and current_price >= tp:
            return {"reason": "take_profit", "price": current_price, "target": tp}
        if sl and current_price <= sl:
            return {"reason": "stop_loss", "price": current_price, "target": sl}
        return None


exit_manager = ExitManager()