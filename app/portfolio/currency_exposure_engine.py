from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from collections import defaultdict


@dataclass
class CurrencyExposureReport:
    currency_exposures: Dict[str, float]  # e.g. {"USD": -2.0, "EUR": 1.0, "GBP": 1.0}
    max_currency: str
    max_currency_exposure: float
    is_exposure_limit_exceeded: bool
    blocked_currencies: List[str]
    open_positions_count: int
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "currency_exposures": {k: round(v, 3) for k, v in self.currency_exposures.items()},
            "max_currency": self.max_currency,
            "max_currency_exposure": round(float(self.max_currency_exposure), 3),
            "is_exposure_limit_exceeded": self.is_exposure_limit_exceeded,
            "blocked_currencies": self.blocked_currencies,
            "open_positions_count": self.open_positions_count,
        }


class CurrencyExposureEngine:
    """
    Currency and Asset Exposure Correlation Decomposition Engine.
    Detects aggregate currency overexposure across multiple FX, Commodity, and Crypto positions.
    """

    CURRENCY_PAIRS = {
        "EURUSD": ("EUR", "USD"),
        "GBPUSD": ("GBP", "USD"),
        "USDJPY": ("USD", "JPY"),
        "AUDUSD": ("AUD", "USD"),
        "USDCAD": ("USD", "CAD"),
        "USDCHF": ("USD", "CHF"),
        "NZDUSD": ("NZD", "USD"),
        "EURGBP": ("EUR", "GBP"),
        "EURJPY": ("EUR", "JPY"),
        "GBPJPY": ("GBP", "JPY"),
        "XAUUSD": ("XAU", "USD"),
        "BTCUSD": ("BTC", "USD"),
        "ETHUSD": ("ETH", "USD"),
        "NAS100": ("NAS", "USD"),
        "SPX500": ("SPX", "USD"),
    }

    def __init__(self, max_single_currency_lots: float = 3.0):
        self.max_single_currency_lots = max_single_currency_lots

    def evaluate_exposure(self, open_positions: List[Dict[str, Any]]) -> CurrencyExposureReport:
        currency_totals = defaultdict(float)

        for pos in open_positions:
            asset = pos.get("asset", pos.get("symbol", "")).upper()
            direction = pos.get("direction", "BUY").upper()
            lots = float(pos.get("lots", pos.get("quantity", 1.0)))

            if asset in self.CURRENCY_PAIRS:
                base, quote = self.CURRENCY_PAIRS[asset]
                if direction == "BUY":
                    currency_totals[base] += lots
                    currency_totals[quote] -= lots
                elif direction == "SELL":
                    currency_totals[base] -= lots
                    currency_totals[quote] += lots
            else:
                # Default non-pair asset
                if direction == "BUY":
                    currency_totals[asset] += lots
                else:
                    currency_totals[asset] -= lots

        blocked = []
        max_curr = "NONE"
        max_exp = 0.0

        for curr, exp in currency_totals.items():
            abs_exp = abs(exp)
            if abs_exp > max_exp:
                max_exp = abs_exp
                max_curr = curr
            if abs_exp >= self.max_single_currency_lots:
                blocked.append(curr)

        is_exceeded = len(blocked) > 0

        return CurrencyExposureReport(
            currency_exposures=dict(currency_totals),
            max_currency=max_curr,
            max_currency_exposure=max_exp,
            is_exposure_limit_exceeded=is_exceeded,
            blocked_currencies=blocked,
            open_positions_count=len(open_positions),
            details={"max_allowed_lots": self.max_single_currency_lots}
        )

    def can_open_new_position(
        self,
        new_asset: str,
        new_direction: str,
        new_lots: float,
        open_positions: List[Dict[str, Any]]
    ) -> (bool, Optional[str]):
        # Simulate adding the position
        simulated_positions = list(open_positions) + [{
            "asset": new_asset,
            "direction": new_direction,
            "lots": new_lots
        }]

        report = self.evaluate_exposure(simulated_positions)
        if report.is_exposure_limit_exceeded:
            return False, f"Opening {new_direction} on {new_asset} exceeds max correlated exposure on: {', '.join(report.blocked_currencies)}"
        return True, None
