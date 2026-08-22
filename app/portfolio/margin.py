from app.logs.logger import get_logger

logger = get_logger(__name__)


class MarginManager:
    def __init__(self, initial_balance: float = 100000.0):
        self._balance = initial_balance
        self._used_margin = 0.0

    def calculate_margin(self, quantity: float, price: float, leverage: float = 10.0) -> float:
        if leverage <= 0:
            return quantity * price
        return quantity * price / leverage

    def use_margin(self, amount: float) -> bool:
        if self._used_margin + amount > self._balance:
            return False
        self._used_margin += amount
        return True

    def release_margin(self, amount: float):
        self._used_margin = max(0, self._used_margin - amount)

    @property
    def free_margin(self) -> float:
        return self._balance - self._used_margin

    @property
    def margin_level(self) -> float:
        if self._used_margin <= 0:
            return 9999.0
        return self._balance / self._used_margin * 100

    def calculate_leverage(self, exposure: float, equity: float) -> float:
        if exposure <= 0:
            return 0.0
        return equity / exposure

    def check_margin_call(self, equity: float, exposure: float, maintenance_margin: float = 0.1) -> bool:
        if exposure <= 0:
            return False
        return (equity / exposure) < maintenance_margin


margin_manager = MarginManager()