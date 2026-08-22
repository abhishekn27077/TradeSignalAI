from typing import Any


class ExposureMonitor:
    def evaluate(self, active_trades: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Stub calculation for portfolio exposure.
        """
        # For stub purposes, assume $100k account, 50% exposed across 3 trades
        return {
            "total_exposure_pct": 50.0,
            "currency_exposure": {
                "USD": 30.0,
                "EUR": -10.0,
                "GBP": 20.0
            },
            "warnings": [
                "High USD exposure detected (30%).",
                "Potential duplicate signals for EUR/USD."
            ]
        }

exposure_monitor = ExposureMonitor()
